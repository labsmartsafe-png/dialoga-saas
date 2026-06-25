"""
Modelos SQLAlchemy do WhatsFlow.

Define as entidades principais: User, Flow, Lead, Template, Conversation, Message.
"""
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Text, DateTime, Boolean, ForeignKey, JSON, Float
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.mutable import MutableDict
from .database import Base


def utcnow():
    """Retorna datetime atual em UTC com timezone-aware."""
    return datetime.now(timezone.utc)


class User(Base):
    """Usuário do sistema (empresa)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    plan = Column(String(50), default="basico")  # basico, profissional, enterprise
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    flows = relationship("Flow", back_populates="owner", cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="owner", cascade="all, delete-orphan")


class Template(Base):
    """Template de chatbot disponível para importação."""
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    icon = Column(String(50), default="🤖")
    # Estrutura do fluxo (JSON)
    flow_data = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)


class Flow(Base):
    """Fluxo de chatbot criado por um usuário."""
    __tablename__ = "flows"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    # Nós do fluxo armazenados como JSON
    nodes = Column(JSON, nullable=False, default=list)
    # Estado inicial (id do primeiro nó)
    start_node_id = Column(String(100), nullable=True)
    active = Column(Boolean, default=True)
    template_slug = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    owner = relationship("User", back_populates="flows")
    leads = relationship("Lead", back_populates="flow")
    conversations = relationship(
        "Conversation", back_populates="flow", cascade="all, delete-orphan"
    )


class Lead(Base):
    """Lead capturado por um fluxo."""
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    flow_id = Column(Integer, ForeignKey("flows.id"), nullable=True)
    name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True, index=True)
    email = Column(String(255), nullable=True)
    # Etapa em que o lead parou
    stage = Column(String(255), nullable=True)
    # Contexto/varáveis capturadas durante a conversa
    context = Column(MutableDict.as_mutable(JSON), nullable=True, default=dict)
    source = Column(String(50), default="simulator")  # simulator | whatsapp
    status = Column(String(50), default="novo")  # novo, qualificado, convertido, perdido
    created_at = Column(DateTime, default=utcnow, index=True)

    owner = relationship("User", back_populates="leads")
    flow = relationship("Flow", back_populates="leads")


class Conversation(Base):
    """Histórico de uma conversa (real ou simulada)."""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    flow_id = Column(Integer, ForeignKey("flows.id"), nullable=False)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True)
    user_phone = Column(String(50), nullable=True, index=True)
    channel = Column(String(50), default="simulator")  # simulator | whatsapp
    # Estado atual da conversa (id do nó atual + contexto) - MutableDict detecta mutações
    state = Column(MutableDict.as_mutable(JSON), nullable=True, default=dict)
    is_active = Column(Boolean, default=True)
    started_at = Column(DateTime, default=utcnow)
    ended_at = Column(DateTime, nullable=True)

    flow = relationship("Flow", back_populates="conversations")
    messages = relationship(
        "Message", back_populates="conversation",
        cascade="all, delete-orphan", order_by="Message.created_at"
    )


class Message(Base):
    """Mensagem individual dentro de uma conversa."""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    direction = Column(String(20), nullable=False)  # inbound | outbound
    sender = Column(String(50), nullable=False)  # user | bot | system
    content = Column(Text, nullable=False)
    node_id = Column(String(100), nullable=True)
    message_type = Column(String(50), default="text")
    created_at = Column(DateTime, default=utcnow)

    conversation = relationship("Conversation", back_populates="messages")
