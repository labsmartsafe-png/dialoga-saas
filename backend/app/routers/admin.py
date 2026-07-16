"""
Fase E.1 — Painel Admin básico.

Acesso permitido quando:
- User.is_admin=True no banco; OU
- email do usuário está em ADMIN_EMAILS (env var, separado por vírgula).
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..config import settings
from ..database import get_db
from ..models import Appointment, Conversation, Flow, Lead, PendingBillingAccount, Subscription, User
from ..models_rag import AISettings, KnowledgeBase
from ..models_whatsapp import WhatsAppConnection
from ..services import plan_limits, billing_service

router = APIRouter()


class AdminUserUpdate(BaseModel):
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    plan: Optional[str] = Field(None, max_length=50)


class PendingBillingClaimRequest(BaseModel):
    user_id: Optional[int] = None


def _admin_email_set() -> set[str]:
    raw = getattr(settings, "admin_emails", "") or ""
    return {e.strip().lower() for e in raw.split(",") if e.strip()}


def is_admin_user(user: User) -> bool:
    return bool(getattr(user, "is_admin", False)) or (user.email or "").lower() in _admin_email_set()


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not is_admin_user(current_user):
        raise HTTPException(403, "Acesso restrito ao administrador.")
    return current_user


def _user_summary(db: Session, user: User) -> dict:
    flows_count = db.query(Flow).filter(Flow.owner_id == user.id).count()
    leads_count = db.query(Lead).filter(Lead.owner_id == user.id).count()
    real_leads_count = db.query(Lead).filter(Lead.owner_id == user.id, Lead.source != "simulator").count()
    connections_count = db.query(WhatsAppConnection).filter(WhatsAppConnection.owner_id == user.id).count()
    appointments_count = db.query(Appointment).filter(Appointment.owner_id == user.id).count()
    kb_count = db.query(KnowledgeBase).filter(KnowledgeBase.owner_id == user.id).count()
    ai = db.query(AISettings).filter(AISettings.owner_id == user.id).first()
    return {
        "id": user.id,
        "email": user.email,
        "company_name": user.company_name,
        "full_name": user.full_name,
        "phone": user.phone,
        "plan": user.plan,
        "is_active": user.is_active,
        "is_admin": bool(getattr(user, "is_admin", False)) or (user.email or "").lower() in _admin_email_set(),
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "flows_count": flows_count,
        "leads_count": leads_count,
        "real_leads_count": real_leads_count,
        "connections_count": connections_count,
        "appointments_count": appointments_count,
        "knowledge_bases_count": kb_count,
        "monthly_ai_used": ai.monthly_ai_used if ai else 0,
        "monthly_ai_limit": ai.monthly_ai_limit if ai else 0,
        "plan_limits": plan_limits.limits_for(user),
    }


def _pending_summary(p: PendingBillingAccount) -> dict:
    return {
        "id": p.id,
        "provider": p.provider,
        "external_id": p.external_id,
        "buyer_email": p.buyer_email,
        "plan": p.plan,
        "status": p.status,
        "product_name": p.product_name,
        "claimed_user_id": p.claimed_user_id,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "claimed_at": p.claimed_at.isoformat() if p.claimed_at else None,
    }


@router.get("/plans")
def admin_plans(admin: User = Depends(require_admin)):
    """Tabela de limites dos planos disponíveis."""
    return plan_limits.public_plan_table()


@router.get("/overview")
def admin_overview(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    users_total = db.query(User).count()
    users_active = db.query(User).filter(User.is_active == True).count()  # noqa: E712
    return {
        "subscriptions_total": db.query(Subscription).count(),
        "subscriptions_active": db.query(Subscription).filter(Subscription.status == "active").count(),
        "pending_billing_total": db.query(PendingBillingAccount).filter(PendingBillingAccount.status == "pending").count(),
        "users_total": users_total,
        "users_active": users_active,
        "flows_total": db.query(Flow).count(),
        "leads_total": db.query(Lead).count(),
        "real_leads_total": db.query(Lead).filter(Lead.source != "simulator").count(),
        "appointments_total": db.query(Appointment).count(),
        "whatsapp_connections_total": db.query(WhatsAppConnection).count(),
        "knowledge_bases_total": db.query(KnowledgeBase).count(),
        "conversations_total": db.query(Conversation).count(),
        "admin_email_mode": bool(_admin_email_set()),
    }


@router.get("/users")
def admin_list_users(
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    query = db.query(User)
    if q:
        like = f"%{q.lower()}%"
        query = query.filter((User.email.ilike(like)) | (User.company_name.ilike(like)))
    users = query.order_by(User.created_at.desc()).all()
    return [_user_summary(db, u) for u in users]


@router.get("/pending-billing")
def admin_pending_billing(
    status: Optional[str] = "pending",
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Lista compras pendentes/claimed/canceled para acompanhamento."""
    q = db.query(PendingBillingAccount)
    if status:
        q = q.filter(PendingBillingAccount.status == status)
    items = q.order_by(PendingBillingAccount.created_at.desc()).limit(200).all()
    return [_pending_summary(p) for p in items]


@router.post("/pending-billing/{pending_id}/claim")
def admin_claim_pending_billing(
    pending_id: int,
    payload: PendingBillingClaimRequest = PendingBillingClaimRequest(),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Vincula compra pendente a usuário existente.

    Se user_id não for informado, tenta encontrar usuário pelo email comprador.
    """
    pending = db.query(PendingBillingAccount).filter(PendingBillingAccount.id == pending_id).first()
    if not pending:
        raise HTTPException(404, "Compra pendente não encontrada.")
    if pending.status != "pending":
        raise HTTPException(400, "Compra não está pendente.")

    user = None
    if payload.user_id:
        user = db.query(User).filter(User.id == payload.user_id).first()
    else:
        user = db.query(User).filter(User.email == pending.buyer_email).first()
    if not user:
        raise HTTPException(404, "Usuário para vincular não encontrado.")

    billing_service.claim_pending_for_user(db, user)
    db.commit()
    db.refresh(pending)
    return {"ok": True, "pending": _pending_summary(pending), "user": _user_summary(db, user)}


@router.post("/pending-billing/{pending_id}/ignore")
def admin_ignore_pending_billing(
    pending_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Marca compra pendente como ignorada."""
    pending = db.query(PendingBillingAccount).filter(PendingBillingAccount.id == pending_id).first()
    if not pending:
        raise HTTPException(404, "Compra pendente não encontrada.")
    pending.status = "ignored"
    db.commit()
    db.refresh(pending)
    return {"ok": True, "pending": _pending_summary(pending)}


@router.put("/users/{user_id}")
def admin_update_user(
    user_id: int,
    payload: AdminUserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Usuário não encontrado.")

    if payload.is_active is not None:
        # evita o admin logado se desativar sem querer
        if user.id == admin.id and payload.is_active is False:
            raise HTTPException(400, "Você não pode desativar sua própria conta admin.")
        user.is_active = payload.is_active
    if payload.is_admin is not None:
        if user.id == admin.id and payload.is_admin is False and (user.email or "").lower() not in _admin_email_set():
            raise HTTPException(400, "Você não pode remover seu próprio admin sem ADMIN_EMAILS.")
        user.is_admin = payload.is_admin
    if payload.plan is not None:
        user.plan = plan_limits.normalize_plan(payload.plan.strip() or user.plan)
        plan_limits.sync_ai_limit_for_user(db, user)
    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return _user_summary(db, user)
