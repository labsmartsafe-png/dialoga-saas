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
from ..models import Appointment, BillingWebhookEvent, Conversation, Flow, Lead, PendingBillingAccount, Subscription, User
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


def _subscription_summary(db: Session, sub: Subscription) -> dict:
    user = db.query(User).filter(User.id == sub.owner_id).first()
    return {
        "id": sub.id,
        "owner_id": sub.owner_id,
        "user_email": user.email if user else None,
        "company_name": user.company_name if user else None,
        "provider": sub.provider,
        "external_id": sub.external_id,
        "plan": sub.plan,
        "status": sub.status,
        "buyer_email": sub.buyer_email,
        "product_name": sub.product_name,
        "started_at": sub.started_at.isoformat() if sub.started_at else None,
        "canceled_at": sub.canceled_at.isoformat() if sub.canceled_at else None,
        "created_at": sub.created_at.isoformat() if sub.created_at else None,
        "updated_at": sub.updated_at.isoformat() if sub.updated_at else None,
    }


def _billing_event_summary(ev) -> dict:
    return {
        "id": ev.id,
        "provider": ev.provider,
        "external_event_id": ev.external_event_id,
        "event_type": ev.event_type,
        "buyer_email": ev.buyer_email,
        "status": ev.status,
        "error": ev.error,
        "received_at": ev.received_at.isoformat() if ev.received_at else None,
        "processed_at": ev.processed_at.isoformat() if ev.processed_at else None,
    }


def _health_item(key: str, label: str, status: str, message: str, *, secret: bool = False) -> dict:
    return {"key": key, "label": label, "status": status, "message": message, "secret": secret}


def _present(value: str | None) -> bool:
    return bool(str(value or "").strip())


@router.get("/system-health")
def admin_system_health(admin: User = Depends(require_admin)):
    """Checklist de saúde para produção/go-live.

    Não expõe valores secretos; apenas indica ausente/configurado e alerta riscos.
    """
    items = []

    default_secret = "chave-padrao-desenvolvimento" in (settings.secret_key or "")
    items.append(_health_item(
        "secret_key", "SECRET_KEY", "error" if default_secret else "ok",
        "Troque a SECRET_KEY padrão antes de produção." if default_secret else "SECRET_KEY configurada.",
        secret=True,
    ))
    items.append(_health_item(
        "database_url", "DATABASE_URL", "ok" if _present(settings.database_url) else "error",
        "Banco configurado." if _present(settings.database_url) else "DATABASE_URL ausente.",
        secret=True,
    ))
    cors = settings.cors_origins or ""
    items.append(_health_item(
        "cors_origins", "CORS_ORIGINS", "warn" if "localhost" in cors and "dialoga-frontend" not in cors else "ok",
        "CORS ainda parece conter apenas localhost; confirme domínio de produção." if "localhost" in cors and "dialoga-frontend" not in cors else "CORS configurado.",
    ))
    items.append(_health_item(
        "wa_fernet_keys", "WA_FERNET_KEYS", "ok" if _present(settings.wa_fernet_keys) else "error",
        "Chave Fernet configurada." if _present(settings.wa_fernet_keys) else "WA_FERNET_KEYS ausente: tokens não podem ser criptografados.",
        secret=True,
    ))

    # Evolution / QR
    if settings.evolution_enabled:
        ok = _present(settings.evolution_base_url) and _present(settings.evolution_global_api_key) and _present(settings.public_base_url)
        items.append(_health_item(
            "evolution", "Evolution API / QR", "ok" if ok else "error",
            "Evolution configurada." if ok else "Evolution habilitada, mas faltam BASE_URL, API_KEY ou PUBLIC_BASE_URL.",
            secret=True,
        ))
    else:
        items.append(_health_item("evolution", "Evolution API / QR", "warn", "Evolution desabilitada."))

    # Gemini
    items.append(_health_item(
        "gemini", "Gemini IA", "ok" if _present(settings.gemini_api_key) else "warn",
        "GEMINI_API_KEY configurada." if _present(settings.gemini_api_key) else "GEMINI_API_KEY ausente: IA/RAG/áudio podem falhar.",
        secret=True,
    ))
    if (settings.gemini_chat_model or "") == "gemini-2.0-flash":
        items.append(_health_item("gemini_model", "GEMINI_CHAT_MODEL", "warn", "Modelo padrão antigo detectado. Recomenda-se gemini-2.5-flash ou flash-lite."))
    else:
        items.append(_health_item("gemini_model", "GEMINI_CHAT_MODEL", "ok", f"Modelo: {settings.gemini_chat_model}"))

    # Google Calendar
    if settings.google_calendar_enabled:
        ok = _present(settings.google_client_id) and _present(settings.google_client_secret)
        items.append(_health_item(
            "google_calendar", "Google Calendar", "ok" if ok else "error",
            "Google Calendar habilitado e credenciais configuradas." if ok else "Google Calendar habilitado, mas faltam CLIENT_ID/SECRET.",
            secret=True,
        ))
    else:
        items.append(_health_item("google_calendar", "Google Calendar", "warn", "Google Calendar desabilitado."))

    # Billing
    if settings.billing_enabled:
        provider = (settings.billing_provider or "manual").lower()
        token_ok = True
        if provider == "hotmart":
            token_ok = _present(settings.hotmart_webhook_token)
        elif provider == "eduzz":
            token_ok = _present(settings.eduzz_webhook_token)
        items.append(_health_item(
            "billing", "Billing", "ok" if token_ok else "warn",
            f"Billing habilitado ({provider})." if token_ok else f"Billing habilitado ({provider}), mas token de webhook não configurado.",
            secret=True,
        ))
    else:
        items.append(_health_item("billing", "Billing", "warn", "Billing desabilitado; acesso ainda depende de controle manual/webhooks em teste."))

    # Meta
    if settings.whatsapp_meta_enabled:
        meta_ok = _present(settings.meta_app_secret)
        items.append(_health_item(
            "meta", "Meta Cloud API", "warn" if meta_ok else "error",
            "Meta configurada, mas lembre de Business Verification e erro 130497 para Brasil." if meta_ok else "Meta habilitada, mas META_APP_SECRET ausente.",
            secret=True,
        ))
    else:
        items.append(_health_item("meta", "Meta Cloud API", "warn", "Meta Cloud API desabilitada ou em shadow/teste."))

    # Admin / Domínio / go-live
    items.append(_health_item(
        "admin_emails", "ADMIN_EMAILS", "ok" if _present(settings.admin_emails) else "warn",
        "ADMIN_EMAILS configurado." if _present(settings.admin_emails) else "ADMIN_EMAILS ausente: primeiro admin pode depender de is_admin no banco.",
    ))
    render_domain = "onrender.com" in (settings.public_base_url or "") or "onrender.com" in (settings.frontend_base_url or "")
    items.append(_health_item(
        "custom_domain", "Domínio próprio", "warn" if render_domain else "ok",
        "Ainda usando domínio onrender.com. Para go-live, configurar domínio próprio e atualizar OAuth/webhooks." if render_domain else "Domínio próprio parece configurado.",
    ))
    items.append(_health_item(
        "render_plan", "Render", "warn",
        "Se estiver no plano Free, o backend dorme e pode estourar memória. Para go-live, usar plano pago.",
    ))
    items.append(_health_item(
        "legal_pages", "Termos e Privacidade", "warn" if "onrender.com" in (settings.privacy_policy_url or "") else "ok",
        f"Privacidade: {settings.privacy_policy_url} | Termos: {settings.terms_url}. Em produção, usar domínio próprio e revisar juridicamente.",
    ))
    items.append(_health_item(
        "email_official", "E-mail oficial", "warn",
        "E-mails atuais são temporários. Antes de produção, configurar domínio/e-mail oficial, SPF/DKIM/DMARC e provedor transacional.",
    ))

    counts = {"ok": 0, "warn": 0, "error": 0}
    for item in items:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    overall = "error" if counts["error"] else ("warn" if counts["warn"] else "ok")
    return {"overall": overall, "counts": counts, "items": items}


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


@router.get("/subscriptions")
def admin_subscriptions(
    status: Optional[str] = None,
    provider: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    q = db.query(Subscription)
    if status:
        q = q.filter(Subscription.status == status)
    if provider:
        q = q.filter(Subscription.provider == provider)
    items = q.order_by(Subscription.updated_at.desc()).limit(300).all()
    return [_subscription_summary(db, s) for s in items]


@router.get("/billing-events")
def admin_billing_events(
    status: Optional[str] = None,
    provider: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    q = db.query(BillingWebhookEvent)
    if status:
        q = q.filter(BillingWebhookEvent.status == status)
    if provider:
        q = q.filter(BillingWebhookEvent.provider == provider)
    items = q.order_by(BillingWebhookEvent.received_at.desc()).limit(300).all()
    return [_billing_event_summary(e) for e in items]


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
