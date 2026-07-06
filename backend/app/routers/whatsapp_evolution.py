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
from ..models import Conversation, Message, Flow
from ..models_whatsapp import WhatsAppConnection, WhatsAppInboundEvent, WhatsAppContactState
from ..services import evolution_service as evo
from ..services import flow_engine

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
    if key.get("fromMe"):
        return  # ignora o que nos mesmos enviamos
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
