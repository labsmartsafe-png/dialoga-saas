"""
Modelos da Fase A — IA + RAG (base de conhecimento por cliente).

Tabelas NOVAS, aditivas (mesmo Base, criadas por create_all). Estilo Column(...) clássico.

PORTABILIDADE SQLite (dev) x Postgres+pgvector (prod):
- O embedding e' guardado em coluna JSON (lista de floats) -> funciona em AMBOS sem pgvector.
- A busca por similaridade e' feita em Python (cosseno) no servico de RAG -> funciona em dev.
- Em producao, quando o volume justificar, migramos a busca para pgvector (operador <=>),
  criando um indice; o dado em JSON pode ser copiado para uma coluna Vector. Nada disso quebra
  o modelo atual (e' evolucao aditiva).

Assim voce desenvolve/testa 100% local em SQLite, sem instalar Postgres.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Integer, Text, DateTime, Boolean, ForeignKey, JSON, Float,
    UniqueConstraint, Index,
)
from sqlalchemy.orm import relationship

from .database import Base


def utcnow():
    return datetime.now(timezone.utc)


class KnowledgeBase(Base):
    """
    Base de conhecimento de um usuario (tenant). Agrupa os documentos/conteudos
    que a IA pode usar para responder (RAG). 1 User -> N bases (ex: por fluxo/numero).
    """
    __tablename__ = "knowledge_bases"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    owner = relationship("User")
    chunks = relationship(
        "KnowledgeChunk", back_populates="knowledge_base",
        cascade="all, delete-orphan",
    )


class KnowledgeChunk(Base):
    """
    Um pedaco (chunk) de conteudo + seu embedding.
    embedding: lista de floats (JSON) — dimensao definida em config (default 768).
    source: de onde veio (nome do arquivo, 'faq', 'texto', url...).
    """
    __tablename__ = "knowledge_chunks"

    id = Column(Integer, primary_key=True, index=True)
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    source = Column(String(255), nullable=True)
    chunk_index = Column(Integer, default=0)
    embedding = Column(JSON, nullable=True)        # lista de floats; None se ainda nao gerado
    embedding_model = Column(String(100), nullable=True)
    token_estimate = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    knowledge_base = relationship("KnowledgeBase", back_populates="chunks")

    __table_args__ = (
        Index("ix_kchunk_kb", "knowledge_base_id"),
    )


class AISettings(Base):
    """
    Configuracoes de comportamento da IA por usuario (tenant).
    Controla persona, regras, fallback e creditos de IA (para proteger custo por plano).
    """
    __tablename__ = "ai_settings"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    enabled = Column(Boolean, default=True)
    persona = Column(Text, nullable=True)              # "Voce e' a recepcionista da Clinica X..."
    tone = Column(String(50), default="cordial")       # cordial | formal | descontraido
    forbidden_topics = Column(JSON, nullable=True)     # lista de temas proibidos
    fallback_message = Column(Text, nullable=True,
                              default="Vou te transferir para um atendente. Um momento, por favor.")
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=True)

    # Creditos / limite de IA por mes (proteje margem)
    monthly_ai_limit = Column(Integer, default=1000)
    monthly_ai_used = Column(Integer, default=0)
    usage_period = Column(String(7), nullable=True)    # "AAAA-MM" do contador atual

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    owner = relationship("User")

    __table_args__ = (
        UniqueConstraint("owner_id", name="uq_ai_settings_owner"),
    )
