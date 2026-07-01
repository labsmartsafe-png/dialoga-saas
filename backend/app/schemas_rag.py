"""Schemas da Fase A (IA + RAG). Estilo schemas.py."""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None


class KnowledgeBaseOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class IndexTextRequest(BaseModel):
    text: str = Field(..., min_length=1)
    source: Optional[str] = "texto"


class AISettingsUpdate(BaseModel):
    enabled: Optional[bool] = None
    persona: Optional[str] = None
    tone: Optional[str] = None
    forbidden_topics: Optional[List[str]] = None
    fallback_message: Optional[str] = None
    knowledge_base_id: Optional[int] = None
    monthly_ai_limit: Optional[int] = None


class AISettingsOut(BaseModel):
    id: int
    enabled: bool
    persona: Optional[str] = None
    tone: str
    forbidden_topics: Optional[List[str]] = None
    fallback_message: Optional[str] = None
    knowledge_base_id: Optional[int] = None
    monthly_ai_limit: int
    monthly_ai_used: int

    class Config:
        from_attributes = True


class AIAskRequest(BaseModel):
    knowledge_base_id: int
    question: str = Field(..., min_length=1, max_length=2000)
