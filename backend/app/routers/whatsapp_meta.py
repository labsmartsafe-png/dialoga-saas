"""
Webhook da Meta Cloud API — FASE 1 (modo SHADOW).

O que esta fase FAZ:
- GET  /webhook/whatsapp/meta  -> handshake (challenge em texto puro)
- POST /webhook/whatsapp/meta  -> valida HMAC sobre o CORPO CRU, parseia defensivamente,
                                   DEDUPLICA, persiste WhatsAppInboundEvent + (para mensagens)
                                   grava Message inbound na Conversation existente.
- Responde SEMPRE 200 rapido (exceto assinatura invalida -> 403).

O que esta fase NAO FAZ (de proposito):
- NAO roda o flow engine.
- NAO envia nenhuma resposta ao usuario.
- So liga se settings.whatsapp_meta_enabled == True. Com a flag OFF, o POST so loga e
  responde 200 (comportamento inerte, identico ao webhook legado).

Tudo aditivo: este router e' incluido em main.py SEM remover o webhook_router legado.
"""

import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Request, Query, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from ..config import settings
from ..database import SessionLocal
from ..models import Conversation, Message, Flow
from ..models_whatsapp import WhatsAppConnection, WhatsAppInboundEvent, WhatsAppContactState

logger = logging.getLogger("whatsflow.whatsapp.meta")

meta_webhook_router = APIRouter()


# --------------------------------------------------------------------------- #
# Validacao de assinatura (App Secret) sobre o CORPO CRU
# --------------------------------------------------------------------------- #
def verify_meta_signature(raw_body: bytes, header: str | None) -> bool:
    """
    Valida X-Hub-Signature-256 = 'sha256=<hex>' usando o META_APP_SECRET.
    Comparacao tempo-constante. Se nao houver app secret configurado, recusa.
    """
    app_secret = settings.meta_app_secret
    if not app_secret:
        logger.warning("meta_app_secret nao configurado; rejeitando POST do webhook Meta.")
        return False
    if not header or not header.startswith("sha256="):
        return False
    received = header.split("sha256=", 1)[1].strip()
    expected = hmac.new(app_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, received)


# --------------------------------------------------------------------------- #
# Parsing defensivo do payload (mensagens + status)
# --------------------------------------------------------------------------- #
def iter_inbound(payload: dict):
    """Gera dicts normalizados a partir do payload bruto da Meta. Tolerante a None."""
    for entry in payload.get("entry", []) or []:
        for change in entry.get("changes", []) or []:
            value = change.get("value", {}) or {}
            metadata = value.get("metadata", {}) or {}
            pnid = metadata.get("phone_number_id")
            contacts = value.get("contacts", []) or []

            for msg in value.get("messages", []) or []:
                wamid = msg.get("id")
                if not wamid:
                    continue
                yield {
                    "kind": "message",
                    "phone_number_id": pnid,
                    "external_id": f"msg:{wamid}",
                    "wamid": wamid,
                    "from": msg.get("from"),
                    "msg_type": msg.get("type"),
                    "message": msg,
                    "contacts": contacts,
                }

            for st in value.get("statuses", []) or []:
                sid = st.get("id")
                if not sid:
                    continue
                # status reusa o mesmo wamid em sent/delivered/read/failed -> chave composta
                yield {
                    "kind": "status",
                    "phone_number_id": pnid,
                    "external_id": f"status:{sid}:{st.get('status')}:{st.get('timestamp')}",
                    "status_obj": st,
                }


def extract_user_input(msg: dict) -> str | None:
    """Normaliza a entrada do usuario para o vocabulario do flow engine."""
    t = msg.get("type")
    if t == "text":
        return (msg.get("text") or {}).get("body")
    if t == "interactive":
        it = msg.get("interactive") or {}
        if it.get("type") == "button_reply":
            return (it.get("button_reply") or {}).get("id")
        if it.get("type") == "list_reply":
            return (it.get("list_reply") or {}).get("id")
    if t == "button":
        return (msg.get("button") or {}).get("payload")
    if t == "location":
        loc = msg.get("location") or {}
        return f"{loc.get('latitude')},{loc.get('longitude')}"
    # midia (image/audio/document/video/sticker): vem media id; tratado em fase futura
    return None


def _contact_name(contacts: list, wa_id: str | None) -> str | None:
    for c in contacts or []:
        if c.get("wa_id") == wa_id:
            return (c.get("profile") or {}).get("name")
    return None


# --------------------------------------------------------------------------- #
# Persistencia (dedup + evento + mensagem inbound) — sync, Session propria
# --------------------------------------------------------------------------- #
def _try_record_event(db: Session, provider: str, external_id: str,
                      event_type: str, raw: dict, connection_id: int | None) -> bool:
    """
    Tenta inserir o evento. Retorna True se NOVO, False se ja existia (dedup).
    Usa a UNIQUE(provider, external_id) como fonte da verdade.
    """
    exists = (
        db.query(WhatsAppInboundEvent.id)
        .filter(WhatsAppInboundEvent.provider == provider,
                WhatsAppInboundEvent.external_id == external_id)
        .first()
    )
    if exists:
        return False
    ev = WhatsAppInboundEvent(
        provider=provider,
        connection_id=connection_id,
        external_id=external_id,
        event_type=event_type,
        raw_payload=raw,
        status="processed",  # na fase shadow nao ha worker; marca como processado
        processed_at=datetime.now(timezone.utc),
    )
    db.add(ev)
    try:
        db.commit()
        return True
    except Exception:
        # corrida: outro request inseriu primeiro -> tratado como duplicata
        db.rollback()
        return False


def _resolve_connection(db: Session, phone_number_id: str | None) -> WhatsAppConnection | None:
    if not phone_number_id:
        return None
    return (
        db.query(WhatsAppConnection)
        .filter(WhatsAppConnection.provider == "meta",
                WhatsAppConnection.phone_number_id == phone_number_id)
        .first()
    )


def _shadow_record_message(db: Session, conn: WhatsAppConnection, item: dict) -> None:
    """
    Em modo shadow: garante Conversation (channel='whatsapp') e grava Message inbound.
    Reaproveita a tabela Conversation existente. NAO roda engine, NAO responde.
    """
    wa_id = item.get("from")
    msg = item.get("message") or {}
    text = extract_user_input(msg) or f"[{item.get('msg_type')}]"

    # Atualiza janela de 24h por contato
    cs = (
        db.query(WhatsAppContactState)
        .filter(WhatsAppContactState.connection_id == conn.id,
                WhatsAppContactState.wa_id == wa_id)
        .first()
    )
    now = datetime.now(timezone.utc)
    if cs is None:
        cs = WhatsAppContactState(connection_id=conn.id, wa_id=wa_id,
                                  last_inbound_at=now, context={})
        db.add(cs)
    else:
        cs.last_inbound_at = now

    # Conversa ativa para este numero/flow (se a conexao tiver flow)
    flow = db.query(Flow).get(conn.flow_id) if conn.flow_id else None
    convo = (
        db.query(Conversation)
        .filter(Conversation.channel == "whatsapp",
                Conversation.user_phone == wa_id,
                Conversation.is_active == True)  # noqa: E712
        .order_by(Conversation.started_at.desc())
        .first()
    )
    if convo is None and flow is not None:
        convo = Conversation(
            flow_id=flow.id,
            channel="whatsapp",
            user_phone=wa_id,
            state={"current_node": flow.start_node_id, "context": {}},
            is_active=True,
        )
        db.add(convo)
        db.flush()

    if convo is not None:
        db.add(Message(
            conversation_id=convo.id,
            direction="inbound",
            sender="user",
            content=text,
            message_type=item.get("msg_type") or "text",
        ))
    db.commit()


def _process_payload_shadow(payload: dict) -> None:
    """Processa o payload em modo shadow, com Session propria (chamado pos-resposta-200)."""
    db = SessionLocal()
    try:
        for item in iter_inbound(payload):
            pnid = item.get("phone_number_id")
            conn = _resolve_connection(db, pnid)
            connection_id = conn.id if conn else None

            is_new = _try_record_event(
                db, "meta", item["external_id"],
                item["kind"], payload, connection_id,
            )
            if not is_new:
                continue  # duplicata: ignora silenciosamente

            if item["kind"] == "message" and conn is not None:
                try:
                    _shadow_record_message(db, conn, item)
                except Exception as exc:
                    db.rollback()
                    logger.exception("Falha ao gravar mensagem shadow: %s", exc)
            elif item["kind"] == "message" and conn is None:
                logger.warning("Mensagem para phone_number_id desconhecido: %s", pnid)
            # status: na fase shadow apenas registrado (evento ja persistido acima)
    finally:
        db.close()


# --------------------------------------------------------------------------- #
# Rotas
# --------------------------------------------------------------------------- #
@meta_webhook_router.get("/webhook/whatsapp/meta")
def meta_verify(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """Handshake da Meta. Reaproveita settings.whatsapp_verify_token ('dialoga-verify')."""
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        return PlainTextResponse(content=hub_challenge or "")
    return Response(status_code=403)


@meta_webhook_router.post("/webhook/whatsapp/meta")
async def meta_receive(request: Request):
    """
    Recebe eventos da Meta. Le o corpo CRU para validar a assinatura ANTES de parsear.
    Responde 200 rapido. Em modo shadow, processa inline com Session propria (volume baixo).
    """
    raw = await request.body()

    # Flag OFF -> comportamento inerte (apenas 200), nada e' processado.
    if not settings.whatsapp_meta_enabled:
        logger.info("[META WEBHOOK][flag off] corpo de %d bytes ignorado.", len(raw))
        return Response(status_code=200)

    if not verify_meta_signature(raw, request.headers.get("X-Hub-Signature-256")):
        logger.warning("[META WEBHOOK] assinatura invalida -> 403.")
        return Response(status_code=403)

    try:
        payload = json.loads(raw)
    except Exception:
        logger.warning("[META WEBHOOK] JSON invalido; respondendo 200 para evitar retry.")
        return Response(status_code=200)

    # FASE 1: processamento inline (shadow). Em Fase 2 isto vira enqueue no arq.
    try:
        _process_payload_shadow(payload)
    except Exception as exc:
        # nunca deixa o webhook estourar -> sempre 200 para a Meta nao reentregar em loop
        logger.exception("[META WEBHOOK] erro no processamento shadow: %s", exc)

    return Response(status_code=200)
