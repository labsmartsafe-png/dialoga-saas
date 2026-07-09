"""
Webhook da Evolution API (WhatsApp nao-oficial / QR Code).

A Evolution manda eventos para /webhook/whatsapp/evo com o payload:
  { "event": "MESSAGES_UPSERT"|"CONNECTION_UPDATE"|"QRCODE_UPDATED",
    "instance": "<nome da instancia>", "data": {...} }

Autenticacao: a Evolution envia o header Authorization: Bearer <segredo> que NOS
configuramos ao criar a instancia. Validamos esse segredo contra o guardado na conexao.

Fluxo (FASE 5): valida -> roteia pela instancia -> dedup -> processa:
- QRCODE_UPDATED: guarda o QR (base64) na conexao (a UI faz polling p/ exibir)
- CONNECTION_UPDATE: atualiza status (open=connected / connecting / close=disconnected)
- MESSAGES_UPSERT: mensagem recebida -> roda o flow engine -> responde (se a conexao tiver flow)
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Request, Response
from sqlalchemy.orm import Session

from ..config import settings
from ..database import SessionLocal
from ..crypto import decrypt_secret
from ..models import Conversation, Message, Flow, Lead
from ..models_whatsapp import WhatsAppConnection, WhatsAppInboundEvent, WhatsAppContactState
from ..services import evolution_service as evo
from ..services import flow_engine
from ..services import lead_service

logger = logging.getLogger("whatsflow.whatsapp.evo")

evo_webhook_router = APIRouter()


def _find_connection(db: Session, instance_name: str) -> WhatsAppConnection | None:
    if not instance_name:
        return None
    return (
        db.query(WhatsAppConnection)
        .filter(WhatsAppConnection.provider == "evolution",
                WhatsAppConnection.evolution_instance_name == instance_name)
        .first()
    )


def _auth_ok(conn: WhatsAppConnection, auth_header: str | None) -> bool:
    """Valida o Bearer <segredo> contra o webhook_secret guardado na conexao."""
    if not conn or not conn.webhook_secret_enc:
        return False
    if not auth_header or not auth_header.startswith("Bearer "):
        return False
    received = auth_header.split("Bearer ", 1)[1].strip()
    try:
        expected = decrypt_secret(conn.webhook_secret_enc)
    except Exception:
        return False
    return bool(expected) and received == expected


@evo_webhook_router.post("/webhook/whatsapp/evo")
async def evo_webhook(request: Request):
    if not settings.evolution_enabled:
        return Response(status_code=200)  # flag off -> inerte

    try:
        payload = await request.json()
    except Exception:
        return Response(status_code=200)

    event = payload.get("event")
    instance = payload.get("instance")
    data = payload.get("data") or {}
    auth_header = request.headers.get("Authorization")

    db: Session = SessionLocal()
    try:
        conn = _find_connection(db, instance)
        if conn is None:
            logger.warning("[EVO] evento de instancia desconhecida: %s", instance)
            return Response(status_code=200)
        if not _auth_ok(conn, auth_header):
            logger.warning("[EVO] auth invalida para instancia %s", instance)
            return Response(status_code=403)

        if event in ("QRCODE_UPDATED", "qrcode.updated"):
            _handle_qrcode(db, conn, data)
        elif event in ("CONNECTION_UPDATE", "connection.update"):
            _handle_connection(db, conn, data)
        elif event in ("MESSAGES_UPSERT", "messages.upsert"):
            _handle_message(db, conn, data)
        # outros eventos: ignorados
    except Exception as exc:
        logger.exception("[EVO] erro processando webhook: %s", exc)
    finally:
        db.close()
    return Response(status_code=200)


def _handle_qrcode(db: Session, conn: WhatsAppConnection, data: dict):
    """Guarda o QR base64 no context da conexao (a UI le via polling)."""
    qr = data.get("base64") or (data.get("qrcode") or {}).get("base64")
    ctx = dict(getattr(conn, "_qr_holder", {}) or {})
    # guardamos no proprio registro via campo generico: usamos last_error como cache? nao.
    # Melhor: guardar no WhatsAppContactState nao serve. Usamos um campo simples: display_name? nao.
    # Solucao limpa: guardar em conn.webhook_secret? nao. Usamos um cache em memoria via tabela contact_state
    # dedicada a instancia. Para simplicidade e robustez, guardamos em conn via coluna 'last_error'
    # seria hack. Entao usamos WhatsAppContactState com wa_id='__qr__'.
    if qr:
        holder = (
            db.query(WhatsAppContactState)
            .filter(WhatsAppContactState.connection_id == conn.id,
                    WhatsAppContactState.wa_id == "__qr__")
            .first()
        )
        if holder is None:
            holder = WhatsAppContactState(connection_id=conn.id, wa_id="__qr__", context={})
            db.add(holder)
        holder.context = {"qrcode_base64": qr, "updated_at": datetime.now(timezone.utc).isoformat()}
        conn.status = "connecting"
        db.commit()
        logger.info("[EVO] QR atualizado para instancia %s", conn.evolution_instance_name)


def _handle_connection(db: Session, conn: WhatsAppConnection, data: dict):
    state = data.get("state") or (data.get("instance") or {}).get("state")
    mapping = {"open": "connected", "connecting": "connecting", "close": "disconnected"}
    new_status = mapping.get(state, conn.status)
    conn.status = new_status
    if new_status == "connected":
        conn.last_error = None
        # ao conectar, tenta capturar o numero conectado, se vier
        wuid = (data.get("wuid") or "")
        num = evo.normalize_jid(wuid)
        if num:
            conn.phone_number = num
        # limpa o QR guardado
        holder = (
            db.query(WhatsAppContactState)
            .filter(WhatsAppContactState.connection_id == conn.id,
                    WhatsAppContactState.wa_id == "__qr__")
            .first()
        )
        if holder:
            holder.context = {}
    db.commit()
    logger.info("[EVO] instancia %s -> %s", conn.evolution_instance_name, new_status)


def _handle_message(db: Session, conn: WhatsAppConnection, data: dict):
    """Mensagem recebida -> dedup -> roda flow engine -> responde."""
    key = data.get("key") or {}
    from_me = bool(key.get("fromMe"))
    remote = key.get("remoteJid") or ""
    if remote.endswith("@g.us"):
        return  # ignora grupos
    msg_id = key.get("id")
    if not msg_id:
        return

    # dedup por (provider, id)
    external_id = f"msg:{msg_id}"
    exists = (
        db.query(WhatsAppInboundEvent.id)
        .filter(WhatsAppInboundEvent.provider == "evolution",
                WhatsAppInboundEvent.external_id == external_id)
        .first()
    )
    if exists:
        return
    ev = WhatsAppInboundEvent(
        provider="evolution", connection_id=conn.id, external_id=external_id,
        event_type="message", raw_payload=data, status="processing",
    )
    db.add(ev)
    try:
        db.commit()
    except Exception:
        db.rollback()
        return  # corrida: outro processou

    wa_id = evo.normalize_jid(remote)
    text = evo.extract_text_from_message(data.get("message") or {})
    if not text:
        text = "[mensagem sem texto]"

    # janela de 24h por contato
    now = datetime.now(timezone.utc)
    cs = (
        db.query(WhatsAppContactState)
        .filter(WhatsAppContactState.connection_id == conn.id,
                WhatsAppContactState.wa_id == wa_id)
        .first()
    )
    if cs is None:
        cs = WhatsAppContactState(connection_id=conn.id, wa_id=wa_id, last_inbound_at=now, context={})
        db.add(cs)
    else:
        cs.last_inbound_at = now

    # precisa de um flow para responder
    flow = db.query(Flow).get(conn.flow_id) if conn.flow_id else None
    if flow is None:
        logger.warning("[EVO] conexao %s sem flow definido; mensagem registrada mas nao respondida.", conn.id)
        ev.status = "processed"
        db.commit()
        return

    # CRM 1.0.2 — Auto-pausar quando o humano responde manualmente pelo WhatsApp.
    # Mensagens fromMe=true são mensagens enviadas pelo número conectado (humano/manual).
    # Se o humano falou com um lead que estava no bot, pausamos a automação imediatamente.
    if from_me:
        manual_lead = _handle_manual_outbound(db, conn, flow, wa_id, text, now)
        ev.status = "processed"
        ev.processed_at = now
        db.commit()
        if manual_lead is not None:
            logger.info("[EVO] humano assumiu lead %s (%s); bot pausado.", manual_lead.id, wa_id)
        return

    # CRM 1.0.3 — Pausa global da automação desta conexão/numero.
    # Diferente do handoff por lead: aqui nenhum contato desta conexão recebe bot.
    if getattr(conn, "automation_paused", False):
        paused_lead = _record_global_paused_inbound(db, conn, flow, wa_id, text, now)
        ev.status = "processed"
        ev.processed_at = now
        db.commit()
        logger.info("[EVO] automacao global pausada na conexao %s; inbound de %s registrado no lead %s.", conn.id, wa_id, getattr(paused_lead, "id", None))
        return

    # CRM 1.0.1 — Trava de handoff humano.
    # Se este contato já está aguardando/recebendo atendimento humano, o bot NÃO pode
    # iniciar um novo fluxo nem responder automaticamente. Apenas registramos a mensagem.
    handoff_lead = _find_handoff_lead(db, conn, flow, wa_id)
    if handoff_lead is not None:
        _record_handoff_inbound(db, handoff_lead, flow, wa_id, text, now)
        ev.status = "processed"
        ev.processed_at = now
        db.commit()
        logger.info("[EVO] bot pausado para lead %s (%s); mensagem registrada para humano.", handoff_lead.id, wa_id)
        return

    # acha/cria conversa ativa deste contato para este flow
    convo = (
        db.query(Conversation)
        .filter(Conversation.channel == "whatsapp",
                Conversation.user_phone == wa_id,
                Conversation.flow_id == flow.id,
                Conversation.is_active == True)  # noqa: E712
        .order_by(Conversation.started_at.desc())
        .first()
    )
    try:
        is_new_conversation = convo is None
        if convo is None:
            convo = flow_engine.start_conversation(db, flow, user_name=None, user_phone=wa_id, channel="whatsapp")
            # CRM 1.0: a origem real desta conversa é WhatsApp QR/Evolution.
            # O flow_engine cria o lead genérico da conversa; aqui refinamos source e connection_id.
            lead_service.sync_lead_from_conversation(
                db,
                flow,
                convo,
                source=lead_service.SOURCE_WHATSAPP_EVOLUTION,
                connection_id=conn.id,
                stage="inicio",
                status=lead_service.STATUS_EM_ATENDIMENTO,
            )
            db.commit()

        # Em fluxo guiado, a primeira mensagem do WhatsApp é o gatilho que inicia o bot.
        # Ela NÃO deve ser tratada como resposta da primeira pergunta, senão um "Oi" já
        # cairia como resposta inválida em +PERG. No modo Atendente IA, processamos direto.
        if (not is_new_conversation) or getattr(flow, "mode", "guided") == "ai_agent":
            flow_engine.send_user_message(db, convo, flow, text=text)

        # envia de volta ao usuario o que o bot gerou (mensagens outbound novas)
        _send_pending_bot_messages(db, conn, convo, wa_id)
        ev.status = "processed"
        ev.processed_at = now
        db.commit()
    except Exception as exc:
        db.rollback()
        ev.status = "failed"
        ev.last_error = str(exc)[:500]
        db.commit()
        logger.exception("[EVO] falha ao processar msg: %s", exc)


def _record_global_paused_inbound(db: Session, conn: WhatsAppConnection, flow: Flow, wa_id: str, text: str, now: datetime) -> Lead:
    """Registra mensagem inbound quando a automação da conexão está pausada.

    A pausa global é configurada na tela Configurações. Ela não deve acionar o bot.
    Criamos/reutilizamos um lead em atendimento humano para que o contato apareça no CRM.
    """
    # Reusa conversa mais recente deste contato/fluxo, ativa ou não.
    convo = (
        db.query(Conversation)
        .filter(Conversation.channel == "whatsapp",
                Conversation.user_phone == wa_id,
                Conversation.flow_id == flow.id)
        .order_by(Conversation.started_at.desc())
        .first()
    )

    if convo is None:
        convo = Conversation(
            flow_id=flow.id,
            channel="whatsapp",
            user_phone=wa_id,
            state={"current_node": None, "context": {}, "bot_paused": True, "paused_reason": "connection_paused"},
            is_active=False,
            ended_at=now,
        )
        db.add(convo)
        db.flush()

    lead = None
    if convo.lead_id:
        lead = db.query(Lead).filter(Lead.id == convo.lead_id, Lead.owner_id == conn.owner_id).first()

    if lead is None:
        q = (
            db.query(Lead)
            .filter(
                Lead.owner_id == conn.owner_id,
                Lead.flow_id == flow.id,
                Lead.phone == wa_id,
                Lead.source.in_((lead_service.SOURCE_WHATSAPP_EVOLUTION, lead_service.SOURCE_WHATSAPP_GENERIC)),
            )
        )
        if hasattr(Lead, "connection_id"):
            q = q.filter((Lead.connection_id == conn.id) | (Lead.connection_id.is_(None)))
        lead = q.order_by(Lead.created_at.desc()).first()

    if lead is None:
        lead = lead_service.sync_lead_from_conversation(
            db,
            flow,
            convo,
            source=lead_service.SOURCE_WHATSAPP_EVOLUTION,
            connection_id=conn.id,
            stage="automacao_pausada",
            status=lead_service.STATUS_EM_ATENDIMENTO_HUMANO,
        )
    else:
        lead.source = lead_service.SOURCE_WHATSAPP_EVOLUTION if lead.source == lead_service.SOURCE_WHATSAPP_GENERIC else lead.source
        lead.connection_id = getattr(lead, "connection_id", None) or conn.id
        lead.conversation_id = convo.id
        lead.stage = "automacao_pausada"
        lead.status = lead_service.STATUS_EM_ATENDIMENTO_HUMANO
        lead.last_interaction_at = now
        if hasattr(lead, "updated_at"):
            lead.updated_at = now
        convo.lead_id = lead.id

    msg = Message(
        conversation_id=convo.id,
        direction="inbound",
        sender="user",
        content=text or "",
        node_id=None,
        message_type="text_connection_paused",
    )
    db.add(msg)

    convo.is_active = False
    convo.ended_at = now
    state = dict(convo.state or {})
    state["bot_paused"] = True
    state["paused_reason"] = "connection_paused"
    convo.state = state
    return lead


def _handle_manual_outbound(db: Session, conn: WhatsAppConnection, flow: Flow, wa_id: str, text: str, now: datetime) -> Lead | None:
    """Detecta mensagem manual do humano (fromMe=true) e pausa o bot.

    Quando o atendente responde diretamente pelo WhatsApp conectado, a Evolution
    envia a mensagem como fromMe=true. Esse é o sinal de que o humano assumiu.
    A partir daqui, o lead entra em 'em_atendimento_humano' e novas mensagens do
    lead não reiniciam o fluxo.
    """
    # Preferimos conversa ativa: é o caso em que o bot ainda estava conduzindo o fluxo.
    convo = (
        db.query(Conversation)
        .filter(Conversation.channel == "whatsapp",
                Conversation.user_phone == wa_id,
                Conversation.flow_id == flow.id,
                Conversation.is_active == True)  # noqa: E712
        .order_by(Conversation.started_at.desc())
        .first()
    )

    lead = None
    if convo is not None and convo.lead_id:
        lead = db.query(Lead).filter(Lead.id == convo.lead_id, Lead.owner_id == conn.owner_id).first()

    if lead is None:
        q = (
            db.query(Lead)
            .filter(
                Lead.owner_id == conn.owner_id,
                Lead.flow_id == flow.id,
                Lead.phone == wa_id,
                Lead.source.in_((lead_service.SOURCE_WHATSAPP_EVOLUTION, lead_service.SOURCE_WHATSAPP_GENERIC)),
                Lead.status.in_((
                    lead_service.STATUS_NOVO,
                    lead_service.STATUS_EM_ATENDIMENTO,
                    lead_service.STATUS_AGUARDANDO_HUMANO,
                    lead_service.STATUS_EM_ATENDIMENTO_HUMANO,
                )),
            )
        )
        if hasattr(Lead, "connection_id"):
            q = q.filter((Lead.connection_id == conn.id) | (Lead.connection_id.is_(None)))
        lead = q.order_by(Lead.created_at.desc()).first()

    # Se não há lead/conversa conhecida, não cria automação nem pausa nada.
    if lead is None and convo is None:
        return None

    if convo is None and getattr(lead, "conversation_id", None):
        convo = db.query(Conversation).filter(Conversation.id == lead.conversation_id).first()

    if convo is None:
        convo = Conversation(
            flow_id=flow.id,
            channel="whatsapp",
            user_phone=wa_id,
            state={"current_node": None, "context": dict((lead.context if lead else {}) or {}), "bot_paused": True},
            is_active=False,
            ended_at=now,
        )
        db.add(convo)
        db.flush()

    # Registra a mensagem manual no histórico para a futura Inbox Humano.
    msg = Message(
        conversation_id=convo.id,
        direction="outbound",
        sender="human",
        content=text or "",
        node_id=None,
        message_type="text_manual",
    )
    db.add(msg)

    if lead is None:
        lead = lead_service.sync_lead_from_conversation(
            db,
            flow,
            convo,
            source=lead_service.SOURCE_WHATSAPP_EVOLUTION,
            connection_id=conn.id,
            stage="atendimento_manual",
            status=lead_service.STATUS_EM_ATENDIMENTO_HUMANO,
        )
    else:
        convo.lead_id = lead.id
        lead.conversation_id = convo.id
        lead.connection_id = getattr(lead, "connection_id", None) or conn.id
        lead.last_interaction_at = now
        if hasattr(lead, "updated_at"):
            lead.updated_at = now
        # Refina source genérico, se necessário.
        if lead.source == lead_service.SOURCE_WHATSAPP_GENERIC:
            lead.source = lead_service.SOURCE_WHATSAPP_EVOLUTION
        lead.status = lead_service.STATUS_EM_ATENDIMENTO_HUMANO
        lead.stage = "atendimento_manual"

    # Pausa a conversa do bot.
    convo.is_active = False
    convo.ended_at = now
    state = dict(convo.state or {})
    state["bot_paused"] = True
    state["paused_reason"] = "manual_takeover"
    convo.state = state
    return lead


def _find_handoff_lead(db: Session, conn: WhatsAppConnection, flow: Flow, wa_id: str) -> Lead | None:
    """Retorna lead cujo bot está pausado por handoff humano.

    Escopo Evolution/QR: source='whatsapp_evolution', mesmo owner, fluxo, telefone e conexão.
    connection_id é usado quando disponível; se lead antigo não tiver connection_id, ainda assim
    bloqueamos pelo telefone/fluxo/source para não deixar o bot atrapalhar o humano.
    """
    q = (
        db.query(Lead)
        .filter(
            Lead.owner_id == conn.owner_id,
            Lead.flow_id == flow.id,
            Lead.phone == wa_id,
            Lead.source == lead_service.SOURCE_WHATSAPP_EVOLUTION,
            Lead.status.in_(lead_service.HUMAN_HANDOFF_STATUSES),
        )
    )
    if hasattr(Lead, "connection_id"):
        q = q.filter((Lead.connection_id == conn.id) | (Lead.connection_id.is_(None)))
    return q.order_by(Lead.created_at.desc()).first()


def _record_handoff_inbound(db: Session, lead: Lead, flow: Flow, wa_id: str, text: str, now: datetime):
    """Registra inbound recebido enquanto bot está pausado para humano.

    Não chama flow_engine e não envia outbound. A mensagem fica no histórico da conversa
    vinculada ao lead, para a futura Inbox Humano.
    """
    convo = None
    if getattr(lead, "conversation_id", None):
        convo = db.query(Conversation).filter(Conversation.id == lead.conversation_id).first()

    if convo is None:
        convo = (
            db.query(Conversation)
            .filter(Conversation.channel == "whatsapp",
                    Conversation.user_phone == wa_id,
                    Conversation.flow_id == flow.id)
            .order_by(Conversation.started_at.desc())
            .first()
        )

    if convo is None:
        # Fallback raro: cria conversa inativa só para preservar histórico humano.
        convo = Conversation(
            flow_id=flow.id,
            channel="whatsapp",
            user_phone=wa_id,
            state={"current_node": None, "context": dict(lead.context or {}), "bot_paused": True},
            is_active=False,
            ended_at=now,
        )
        db.add(convo)
        db.flush()

    _save_handoff_message = Message(
        conversation_id=convo.id,
        direction="inbound",
        sender="user",
        content=text or "",
        node_id=None,
        message_type="text_handoff",
    )
    db.add(_save_handoff_message)

    lead.conversation_id = convo.id
    lead.last_interaction_at = now
    if hasattr(lead, "updated_at"):
        lead.updated_at = now
    # Mantém status aguardando_humano/em_atendimento_humano; não encerra nem reinicia.
    convo.lead_id = lead.id


def _send_pending_bot_messages(db: Session, conn: WhatsAppConnection, convo: Conversation, wa_id: str):
    """
    Envia via Evolution as mensagens 'bot' desta conversa que ainda nao foram enviadas.
    Marca as enviadas gravando node_id com prefixo (simples): usamos message_type='sent_evo'
    para nao reenviar. Estrategia: enviar as mensagens outbound/bot mais recentes que ainda
    nao tem marca de envio.
    """
    msgs = (
        db.query(Message)
        .filter(Message.conversation_id == convo.id,
                Message.direction == "outbound",
                Message.sender == "bot")
        .order_by(Message.created_at.asc())
        .all()
    )
    for m in msgs:
        if (m.message_type or "").endswith("_sent"):
            continue  # ja enviada
        res = evo.send_text(conn.evolution_instance_name, wa_id, m.content or "")
        if res.get("ok"):
            m.message_type = (m.message_type or "text") + "_sent"
        else:
            logger.warning("[EVO] falha ao enviar resposta: %s", res.get("error"))
    db.commit()
