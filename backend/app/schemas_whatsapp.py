"""
Schemas Pydantic para o modulo de conexoes WhatsApp (Fase 3).
Segue o estilo de schemas.py (BaseModel, from_attributes).
REGRA DE SEGURANCA: nenhum schema de saida expoe o token. So 'last4'.
"""
from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field


class WhatsAppConnectionCreate(BaseModel):
    """Cadastro/atualizacao de conexao Meta. O token vem em texto e e' criptografado no backend."""
    provider: Literal["meta"] = "meta"   # Evolution entra em fase futura
    display_name: Optional[str] = Field(None, max_length=255)
    phone_number_id: str = Field(..., min_length=3, max_length=100)
    access_token: str = Field(..., min_length=10)
    waba_id: Optional[str] = Field(None, max_length=100)
    flow_id: Optional[int] = None        # qual fluxo este numero usa para responder


class WhatsAppConnectionOut(BaseModel):
    """Saida segura: SEM token. Mostra apenas os ultimos 4 digitos para conferencia."""
    id: int
    provider: str
    status: str
    display_name: Optional[str] = None
    phone_number: Optional[str] = None
    phone_number_id: Optional[str] = None
    waba_id: Optional[str] = None
    flow_id: Optional[int] = None
    access_token_last4: Optional[str] = None
    last_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WhatsAppSendTestRequest(BaseModel):
    """Disparo de mensagem de teste por uma conexao."""
    to: str = Field(..., description="Numero com DDI, ex: 5511999999999", min_length=8, max_length=20)
    text: str = Field(..., min_length=1, max_length=1000)


class EvolutionConnectionCreate(BaseModel):
    """Cria uma conexao via QR Code (Evolution/nao-oficial)."""
    display_name: Optional[str] = Field(None, max_length=255)
    flow_id: Optional[int] = None
