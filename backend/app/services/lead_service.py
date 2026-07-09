"""
Serviço central de CRM/Leads do dIAloga+.

Objetivo da Fase CRM 1.0:
- Criar/atualizar lead de forma única para simulador, WhatsApp QR (Evolution)
  e WhatsApp oficial (Meta no futuro).
- Evitar regra de lead espalhada entre flow_engine, webhooks e telas.
- Diferenciar claramente origens: simulator, whatsapp_evolution, whatsapp_meta.

Regra de segurança:
- Código aditivo: usa campos novos opcionais e mantém compatibilidade com leads antigos.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from ..models import Conversation, Flow, Lead


SOURCE_SIMULATOR = "simulator"
SOURCE_WHATSAPP_EVOLUTION = "whatsapp_evolution"
SOURCE_WHATSAPP_META = "whatsapp_meta"
SOURCE_WHATSAPP_GENERIC = "whatsapp"

STATUS_NOVO = "novo"
STATUS_EM_ATENDIMENTO = "em_atendimento"
STATUS_AGUARDANDO_HUMANO = "aguardando_humano"
STATUS_EM_ATENDIMENTO_HUMANO = "em_atendimento_humano"
STATUS_ENCERRADO = "encerrado"

# Enquanto o lead estiver em um destes status, o bot NÃO deve reiniciar fluxo
# nem responder automaticamente. A mensagem é apenas registrada para o humano.
HUMAN_HANDOFF_STATUSES = (STATUS_AGUARDANDO_HUMANO, STATUS_EM_ATENDIMENTO_HUMANO)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def default_source_for_channel(channel: Optional[str]) -> str:
    if channel == "whatsapp":
        return SOURCE_WHATSAPP_GENERIC
    return SOURCE_SIMULATOR


def _safe_context(conv: Conversation) -> Dict[str, Any]:
    state = conv.state or {}
    ctx = state.get("context") or {}
    return dict(ctx) if isinstance(ctx, dict) else {}


def _identity_from_context(ctx: Dict[str, Any], conv: Conversation) -> tuple[Optional[str], Optional[str], Optional[str]]:
    name = ctx.get("nome") or ctx.get("name")
    phone = ctx.get("telefone") or ctx.get("phone") or conv.user_phone
    email = ctx.get("email")
    return name, phone, email


def get_or_create_lead_for_conversation(
    db: Session,
    flow: Flow,
    conv: Conversation,
    *,
    source: Optional[str] = None,
    connection_id: Optional[int] = None,
    stage: Optional[str] = None,
    status: Optional[str] = None,
) -> Lead:
    """Obtém ou cria lead vinculado à conversa.

    Deduplicação conservadora:
    1. Se a conversa já tem lead_id, usa esse lead.
    2. Se for canal real e tiver telefone, reutiliza o lead mais recente do mesmo
       owner/flow/source/telefone para evitar duplicidade em reentrega de webhook.
    3. Caso contrário, cria um lead novo.
    """
    source = source or default_source_for_channel(conv.channel)
    ctx = _safe_context(conv)
    name, phone, email = _identity_from_context(ctx, conv)
    now = utcnow()

    lead = None
    if conv.lead_id:
        lead = db.query(Lead).filter(Lead.id == conv.lead_id, Lead.owner_id == flow.owner_id).first()

    if lead is None and phone and source != SOURCE_SIMULATOR:
        lead = (
            db.query(Lead)
            .filter(
                Lead.owner_id == flow.owner_id,
                Lead.flow_id == flow.id,
                Lead.phone == phone,
                Lead.source == source,
            )
            .order_by(Lead.created_at.desc())
            .first()
        )

    if lead is None:
        lead = Lead(
            owner_id=flow.owner_id,
            flow_id=flow.id,
            name=name,
            phone=phone,
            email=email,
            stage=stage,
            context=ctx,
            source=source,
            status=status or STATUS_NOVO,
        )
        # Campos aditivos podem não existir em bancos muito antigos até a migração rodar;
        # como já estarão no model, setamos normalmente.
        if hasattr(lead, "conversation_id"):
            lead.conversation_id = conv.id
        if hasattr(lead, "connection_id"):
            lead.connection_id = connection_id
        if hasattr(lead, "last_interaction_at"):
            lead.last_interaction_at = now
        if hasattr(lead, "updated_at"):
            lead.updated_at = now
        db.add(lead)
        db.flush()
    else:
        # Atualiza sem apagar informação útil já existente.
        if name:
            lead.name = name
        if phone and not lead.phone:
            lead.phone = phone
        if email:
            lead.email = email
        lead.context = ctx
        if stage:
            lead.stage = stage
        if status:
            lead.status = status
        if source and (not lead.source or lead.source in (SOURCE_WHATSAPP_GENERIC, SOURCE_SIMULATOR)):
            # Permite refinar origem genérica criada pelo flow_engine.
            # Ex.: whatsapp -> whatsapp_evolution, whatsapp -> whatsapp_meta.
            lead.source = source
        if hasattr(lead, "conversation_id") and not getattr(lead, "conversation_id", None):
            lead.conversation_id = conv.id
        if hasattr(lead, "connection_id") and connection_id and not getattr(lead, "connection_id", None):
            lead.connection_id = connection_id
        if hasattr(lead, "last_interaction_at"):
            lead.last_interaction_at = now
        if hasattr(lead, "updated_at"):
            lead.updated_at = now
        db.flush()

    conv.lead_id = lead.id
    return lead


def sync_lead_from_conversation(
    db: Session,
    flow: Flow,
    conv: Conversation,
    *,
    source: Optional[str] = None,
    connection_id: Optional[int] = None,
    stage: Optional[str] = None,
    status: Optional[str] = None,
) -> Lead:
    """Sincroniza o lead com o contexto atual da conversa."""
    return get_or_create_lead_for_conversation(
        db,
        flow,
        conv,
        source=source,
        connection_id=connection_id,
        stage=stage,
        status=status,
    )


def mark_handoff(
    db: Session,
    flow: Flow,
    conv: Conversation,
    *,
    source: Optional[str] = None,
    connection_id: Optional[int] = None,
    stage: str = "atendimento_humano",
) -> Lead:
    return sync_lead_from_conversation(
        db,
        flow,
        conv,
        source=source,
        connection_id=connection_id,
        stage=stage,
        status=STATUS_AGUARDANDO_HUMANO,
    )


def mark_finished(
    db: Session,
    flow: Flow,
    conv: Conversation,
    *,
    source: Optional[str] = None,
    connection_id: Optional[int] = None,
    stage: str = "fim",
) -> Lead:
    return sync_lead_from_conversation(
        db,
        flow,
        conv,
        source=source,
        connection_id=connection_id,
        stage=stage,
        status=STATUS_ENCERRADO,
    )


def mark_manual_takeover(
    db: Session,
    flow: Flow,
    conv: Conversation,
    *,
    source: Optional[str] = None,
    connection_id: Optional[int] = None,
    stage: str = "atendimento_manual",
) -> Lead:
    """Marca que um humano assumiu manualmente e o bot deve ficar pausado."""
    return sync_lead_from_conversation(
        db,
        flow,
        conv,
        source=source,
        connection_id=connection_id,
        stage=stage,
        status=STATUS_EM_ATENDIMENTO_HUMANO,
    )
