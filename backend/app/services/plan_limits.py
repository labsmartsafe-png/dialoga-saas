"""
Fase E.2 — Planos e limites.

Limites simples por plano para proteger margem antes do billing automático.
Compatível com planos legados (basico/enterprise) e novos (essencial/profissional/performance).
"""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models import Flow, User
from ..models_rag import AISettings, KnowledgeBase
from ..models_whatsapp import WhatsAppConnection

PLAN_LIMITS = {
    "basico": {"flows": 3, "whatsapp_connections": 1, "knowledge_bases": 3, "monthly_ai_limit": 500},
    "essencial": {"flows": 3, "whatsapp_connections": 1, "knowledge_bases": 3, "monthly_ai_limit": 500},
    "profissional": {"flows": 10, "whatsapp_connections": 2, "knowledge_bases": 10, "monthly_ai_limit": 2000},
    "performance": {"flows": 50, "whatsapp_connections": 5, "knowledge_bases": 50, "monthly_ai_limit": 10000},
    "enterprise": {"flows": None, "whatsapp_connections": None, "knowledge_bases": None, "monthly_ai_limit": 50000},
    "admin": {"flows": None, "whatsapp_connections": None, "knowledge_bases": None, "monthly_ai_limit": 100000},
}


def normalize_plan(plan: str | None) -> str:
    p = (plan or "essencial").strip().lower()
    return p if p in PLAN_LIMITS else "essencial"


def limits_for(user_or_plan) -> dict:
    plan = user_or_plan if isinstance(user_or_plan, str) else getattr(user_or_plan, "plan", None)
    return PLAN_LIMITS[normalize_plan(plan)]


def _check(resource_label: str, limit: int | None, current: int):
    if limit is not None and current >= limit:
        raise HTTPException(
            403,
            f"Limite do plano atingido para {resource_label}. Limite atual: {limit}. Faça upgrade para continuar.",
        )


def assert_can_create_flow(db: Session, user: User):
    limit = limits_for(user).get("flows")
    current = db.query(Flow).filter(Flow.owner_id == user.id).count()
    _check("fluxos", limit, current)


def assert_can_create_whatsapp_connection(db: Session, user: User):
    limit = limits_for(user).get("whatsapp_connections")
    current = db.query(WhatsAppConnection).filter(WhatsAppConnection.owner_id == user.id).count()
    _check("conexões WhatsApp", limit, current)


def assert_can_create_knowledge_base(db: Session, user: User):
    limit = limits_for(user).get("knowledge_bases")
    current = db.query(KnowledgeBase).filter(KnowledgeBase.owner_id == user.id).count()
    _check("bases de conhecimento", limit, current)


def sync_ai_limit_for_user(db: Session, user: User) -> AISettings:
    """Garante que AISettings.monthly_ai_limit acompanha o plano atual."""
    ai = db.query(AISettings).filter(AISettings.owner_id == user.id).first()
    if ai is None:
        ai = AISettings(owner_id=user.id)
        db.add(ai)
        db.flush()
    ai.monthly_ai_limit = int(limits_for(user).get("monthly_ai_limit") or 100000)
    db.flush()
    return ai


def public_plan_table() -> dict:
    return PLAN_LIMITS
