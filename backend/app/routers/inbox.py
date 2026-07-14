"""
CRM 1.1 — Inbox Humano.

Primeira versão da caixa de atendimento humano:
- lista leads aguardando/recebendo humano;
- mostra histórico de mensagens;
- permite assumir, responder via Evolution e encerrar atendimento.

Escopo inicial: WhatsApp QR/Evolution. A estrutura já fica pronta para Meta depois.
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Conversation, Flow, Lead, LeadNote, Message, User
from ..models_whatsapp import WhatsAppConnection
from ..services import evolution_service as evo
from ..services import lead_service


router = APIRouter()


class InboxSendMessage(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


class InboxStatusUpdate(BaseModel):
    status: Optional[str] = None
    stage: Optional[str] = None


def _now():
    return datetime.now(timezone.utc)


def _owned_lead(db: Session, lead_id: int, user: User) -> Lead:
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.owner_id == user.id).first()
    if not lead:
        raise HTTPException(404, "Lead não encontrado.")
    return lead


def _conversation_for_lead(db: Session, lead: Lead) -> Conversation | None:
    if getattr(lead, "conversation_id", None):
        conv = db.query(Conversation).filter(Conversation.id == lead.conversation_id).first()
        if conv:
            return conv
    if lead.phone and lead.flow_id:
        return (
            db.query(Conversation)
            .filter(Conversation.user_phone == lead.phone,
                    Conversation.flow_id == lead.flow_id,
                    Conversation.channel == "whatsapp")
            .order_by(Conversation.started_at.desc())
            .first()
        )
    return None


def _serialize_message(m: Message) -> dict:
    return {
        "id": m.id,
        "direction": m.direction,
        "sender": m.sender,
        "content": m.content,
        "node_id": m.node_id,
        "message_type": m.message_type,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }


def _serialize_lead(db: Session, lead: Lead) -> dict:
    flow_name = None
    if lead.flow_id:
        flow = db.query(Flow).filter(Flow.id == lead.flow_id).first()
        flow_name = flow.name if flow else None
    return {
        "id": lead.id,
        "flow_id": lead.flow_id,
        "flow_name": flow_name,
        "name": lead.name,
        "phone": lead.phone,
        "email": lead.email,
        "stage": lead.stage,
        "context": lead.context or {},
        "source": lead.source,
        "status": lead.status,
        "tags": lead.tags or [],
        "conversation_id": getattr(lead, "conversation_id", None),
        "connection_id": getattr(lead, "connection_id", None),
        "last_interaction_at": lead.last_interaction_at.isoformat() if getattr(lead, "last_interaction_at", None) else None,
        "created_at": lead.created_at.isoformat() if lead.created_at else None,
    }


def _ensure_conversation(db: Session, lead: Lead) -> Conversation:
    conv = _conversation_for_lead(db, lead)
    if conv:
        return conv
    if not lead.flow_id:
        raise HTTPException(400, "Lead sem fluxo vinculado; não é possível abrir conversa.")
    conv = Conversation(
        flow_id=lead.flow_id,
        lead_id=lead.id,
        user_phone=lead.phone,
        channel="whatsapp",
        state={"current_node": None, "context": dict(lead.context or {}), "bot_paused": True, "paused_reason": "human_inbox"},
        is_active=False,
        ended_at=_now(),
    )
    db.add(conv)
    db.flush()
    lead.conversation_id = conv.id
    return conv


def _connection_for_lead(db: Session, lead: Lead, user: User) -> WhatsAppConnection:
    conn = None
    if getattr(lead, "connection_id", None):
        conn = (
            db.query(WhatsAppConnection)
            .filter(WhatsAppConnection.id == lead.connection_id,
                    WhatsAppConnection.owner_id == user.id)
            .first()
        )
    if conn is None:
        conn = (
            db.query(WhatsAppConnection)
            .filter(WhatsAppConnection.owner_id == user.id,
                    WhatsAppConnection.provider == "evolution",
                    WhatsAppConnection.status == "connected")
            .order_by(WhatsAppConnection.updated_at.desc())
            .first()
        )
    if conn is None:
        raise HTTPException(400, "Nenhuma conexão WhatsApp QR conectada encontrada para enviar mensagem.")
    if conn.provider != "evolution":
        raise HTTPException(400, "Envio pela Inbox nesta fase suporta apenas conexão QR/Evolution.")
    if not conn.evolution_instance_name:
        raise HTTPException(400, "Conexão Evolution sem instância vinculada.")
    return conn


@router.get("/conversations")
def list_inbox_conversations(
    status: Optional[str] = None,
    tag: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista atendimentos humanos da Inbox."""
    statuses = [lead_service.STATUS_AGUARDANDO_HUMANO, lead_service.STATUS_EM_ATENDIMENTO_HUMANO]
    q = db.query(Lead).filter(Lead.owner_id == current_user.id)
    if status:
        q = q.filter(Lead.status == status)
    else:
        q = q.filter(Lead.status.in_(statuses))
    q = q.order_by(Lead.last_interaction_at.desc().nullslast(), Lead.created_at.desc())
    leads = q.all()
    if tag:
        needle = tag.strip().lower()
        leads = [l for l in leads if any(str(t).strip().lower() == needle for t in (l.tags or []))]

    items = []
    for lead in leads:
        conv = _conversation_for_lead(db, lead)
        last_msg = None
        unread_hint = False
        if conv:
            last = (
                db.query(Message)
                .filter(Message.conversation_id == conv.id)
                .order_by(Message.created_at.desc())
                .first()
            )
            if last:
                last_msg = _serialize_message(last)
                unread_hint = last.direction == "inbound"
        item = _serialize_lead(db, lead)
        item["conversation_id"] = conv.id if conv else item.get("conversation_id")
        item["last_message"] = last_msg
        item["unread_hint"] = unread_hint
        items.append(item)
    return items


@router.get("/conversations/{lead_id}")
def get_inbox_conversation(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Detalhe de um atendimento humano."""
    lead = _owned_lead(db, lead_id, current_user)
    conv = _conversation_for_lead(db, lead)
    messages = []
    if conv:
        messages = [
            _serialize_message(m)
            for m in db.query(Message).filter(Message.conversation_id == conv.id).order_by(Message.created_at.asc()).all()
        ]
    notes = [
        {
            "id": n.id,
            "lead_id": n.lead_id,
            "content": n.content,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in db.query(LeadNote)
        .filter(LeadNote.lead_id == lead.id, LeadNote.owner_id == current_user.id)
        .order_by(LeadNote.created_at.desc())
        .all()
    ]
    data = _serialize_lead(db, lead)
    data["conversation_id"] = conv.id if conv else data.get("conversation_id")
    data["messages"] = messages
    data["notes"] = notes
    return data


@router.post("/conversations/{lead_id}/assume")
def assume_conversation(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Assume atendimento humano e pausa o bot para o lead."""
    lead = _owned_lead(db, lead_id, current_user)
    conv = _ensure_conversation(db, lead)
    now = _now()
    lead.status = lead_service.STATUS_EM_ATENDIMENTO_HUMANO
    lead.stage = "atendimento_manual"
    lead.last_interaction_at = now
    if hasattr(lead, "updated_at"):
        lead.updated_at = now
    conv.is_active = False
    conv.ended_at = now
    state = dict(conv.state or {})
    state["bot_paused"] = True
    state["paused_reason"] = "human_inbox_assumed"
    conv.state = state
    db.commit()
    return {"ok": True, "lead": _serialize_lead(db, lead)}


@router.post("/conversations/{lead_id}/send")
def send_human_message(
    lead_id: int,
    payload: InboxSendMessage,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Envia mensagem humana via Evolution e registra no histórico."""
    lead = _owned_lead(db, lead_id, current_user)
    if not lead.phone:
        raise HTTPException(400, "Lead sem telefone.")
    conv = _ensure_conversation(db, lead)
    conn = _connection_for_lead(db, lead, current_user)

    result = evo.send_text(conn.evolution_instance_name, lead.phone, payload.text)
    if not result.get("ok"):
        raise HTTPException(502, result.get("error") or "Falha ao enviar mensagem pela Evolution.")

    now = _now()
    msg = Message(
        conversation_id=conv.id,
        direction="outbound",
        sender="human",
        content=payload.text,
        node_id=None,
        message_type="text_manual_panel",
    )
    db.add(msg)

    lead.status = lead_service.STATUS_EM_ATENDIMENTO_HUMANO
    lead.stage = "atendimento_manual"
    lead.connection_id = getattr(lead, "connection_id", None) or conn.id
    lead.conversation_id = conv.id
    lead.last_interaction_at = now
    if hasattr(lead, "updated_at"):
        lead.updated_at = now
    conv.lead_id = lead.id
    conv.is_active = False
    conv.ended_at = now
    state = dict(conv.state or {})
    state["bot_paused"] = True
    state["paused_reason"] = "human_inbox_send"
    conv.state = state

    db.commit()
    db.refresh(msg)
    return {"ok": True, "message": _serialize_message(msg), "provider_message_id": result.get("provider_message_id")}


@router.post("/conversations/{lead_id}/close")
def close_conversation(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Encerra atendimento humano.

    Depois de encerrado, uma nova mensagem futura pode abrir um novo fluxo, respeitando as
    regras existentes de automação global/pausa por lead.
    """
    lead = _owned_lead(db, lead_id, current_user)
    conv = _conversation_for_lead(db, lead)
    now = _now()
    lead.status = lead_service.STATUS_ENCERRADO
    lead.stage = "atendimento_encerrado"
    lead.last_interaction_at = now
    if hasattr(lead, "updated_at"):
        lead.updated_at = now
    if conv:
        conv.is_active = False
        conv.ended_at = now
        state = dict(conv.state or {})
        state["bot_paused"] = False
        state["closed_by_human"] = True
        conv.state = state
    db.commit()
    return {"ok": True, "lead": _serialize_lead(db, lead)}
