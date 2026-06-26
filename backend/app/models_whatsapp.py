"""
Modelos NOVOS para WhatsApp real + billing.

IMPORTANTE — por que este arquivo é seguro:
- Usa o MESMO Base de app.database (mesmo registry do metadata).
- Só DECLARA tabelas novas -> Base.metadata.create_all() as cria sem tocar nas existentes.
- Mesmo estilo Column(...) clássico do models.py atual (NÃO usa Mapped[]).
- PKs Integer autoincrement, para casar com users.id / flows.id / conversations.id.
- Para que init_db() registre estes modelos, IMPORTE este módulo no final de models.py:
      from .models_whatsapp import *   # noqa
  (init_db já faz `from . import models`, então isto basta para o create_all enxergar tudo.)

NADA aqui altera ou dropa coluna existente.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Integer, Text, DateTime, Boolean, ForeignKey, JSON,
    UniqueConstraint, Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.mutable import MutableDict

from .database import Base


def utcnow():
    """Helper UTC local (evita import circular com models.py)."""
    return datetime.now(timezone.utc)


class WhatsAppConnection(Base):
    """
    Conexão de um usuário (tenant) com o WhatsApp.
    1 User -> N conexões (suporta multi-numero do Enterprise sem migration futura).
    provider: 'meta' (Cloud API oficial) | 'evolution' (QR/nao-oficial).
    Tokens SEMPRE criptografados (campos *_enc) via app.crypto.
    """
    __tablename__ = "whatsapp_connections"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    provider = Column(String(20), nullable=False)            # meta | evolution
    status = Column(String(20), default="disconnected")      # connecting|connected|disconnected|error|disabled
    display_name = Column(String(255), nullable=True)
    phone_number = Column(String(40), nullable=True)
    # Qual fluxo este numero usa para responder (FK opcional para flows)
    flow_id = Column(Integer, ForeignKey("flows.id"), nullable=True)

    # --- Meta Cloud API ---
    phone_number_id = Column(String(100), nullable=True, index=True)  # roteamento multi-tenant
    waba_id = Column(String(100), nullable=True)
    access_token_enc = Column(Text, nullable=True)           # Fernet (texto base64)
    access_token_last4 = Column(String(8), nullable=True)    # so p/ mascarar na UI (nunca decifra p/ exibir)
    last_error = Column(Text, nullable=True)                 # ultima falha (ex: token 190) p/ UI

    # --- Evolution API (QR) ---
    evolution_instance_name = Column(String(150), nullable=True)
    evolution_api_key_enc = Column(Text, nullable=True)
    webhook_secret_enc = Column(Text, nullable=True)         # segredo p/ autenticar webhook Evolution

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    owner = relationship("User", back_populates="whatsapp_connections")
    flow = relationship("Flow")

    __table_args__ = (
        # phone_number_id deve ser unico por provider (roteamento confiavel da Meta)
        UniqueConstraint("provider", "phone_number_id", name="uq_wa_provider_phone_number_id"),
        UniqueConstraint("provider", "evolution_instance_name", name="uq_wa_provider_instance"),
    )


class WhatsAppInboundEvent(Base):
    """
    Log bruto + dedup de TUDO que chega nos webhooks (Meta/Evolution).
    A UNIQUE(provider, external_id) garante idempotencia: reentrega da Meta nao reprocessa.
    O worker consome 'pending' -> processa -> marca 'processed'/'failed'.
    """
    __tablename__ = "whatsapp_inbound_events"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(20), nullable=False)            # meta | evolution
    connection_id = Column(Integer, ForeignKey("whatsapp_connections.id"), nullable=True)
    external_id = Column(String(255), nullable=False)        # msg:{wamid} | status:{wamid}:{status}:{ts}
    event_type = Column(String(50), nullable=False)          # message | status | unknown
    raw_payload = Column(JSON, nullable=False)
    status = Column(String(30), default="pending")           # pending|processing|processed|failed|ignored
    attempts = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    received_at = Column(DateTime, default=utcnow, index=True)
    processed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("provider", "external_id", name="uq_wa_inbound_provider_external"),
        Index("ix_wa_inbound_status", "status"),
    )


class WhatsAppOutboundMessage(Base):
    """
    Outbox: persistir ANTES de enviar (status 'sending') com local_dedup_key.
    Evita envio duplo e permite reconciliar pelo webhook de 'statuses'.
    """
    __tablename__ = "whatsapp_outbound_messages"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("whatsapp_connections.id"), nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)
    recipient_wa_id = Column(String(40), nullable=False, index=True)
    provider_message_id = Column(String(255), nullable=True, index=True)
    local_dedup_key = Column(String(255), nullable=False)
    message_type = Column(String(50), nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String(30), default="queued")            # queued|sending|sent|delivered|read|failed
    error_code = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    sent_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("connection_id", "local_dedup_key", name="uq_wa_outbound_local_dedup"),
    )


class WhatsAppContactState(Base):
    """
    Estado leve por contato/numero: ultima entrada (janela de 24h).
    Permite saber se pode enviar texto livre ou se precisa de template (HSM).
    """
    __tablename__ = "whatsapp_contact_states"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("whatsapp_connections.id"), nullable=False)
    wa_id = Column(String(40), nullable=False)               # numero do contato
    last_inbound_at = Column(DateTime, nullable=True)
    context = Column(MutableDict.as_mutable(JSON), nullable=True, default=dict)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    __table_args__ = (
        UniqueConstraint("connection_id", "wa_id", name="uq_wa_contact_state"),
    )
