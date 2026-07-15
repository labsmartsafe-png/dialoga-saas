"""
Fase E.3 — Billing webhooks Hotmart/Eduzz.

Primeira versão: recebe webhook, identifica comprador por email, mapeia plano,
ativa/desativa usuário e registra assinatura/evento.

Importante: os provedores têm payloads variados; por isso a extração é defensiva.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from ..config import settings
from ..models import BillingWebhookEvent, Subscription, User
from ..services import plan_limits

ACTIVE_STATUSES = {"approved", "complete", "completed", "paid", "active", "trial", "billet_printed"}
INACTIVE_STATUSES = {"canceled", "cancelled", "refunded", "chargeback", "expired", "overdue", "delayed", "dispute"}


def _lower(v: Any) -> str:
    return str(v or "").strip().lower()


def deep_get(data: dict, paths: list[str]) -> Optional[Any]:
    for path in paths:
        cur: Any = data
        ok = True
        for part in path.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                ok = False
                break
        if ok and cur not in (None, ""):
            return cur
    return None


def event_id(provider: str, payload: dict) -> str:
    val = deep_get(payload, ["id", "event_id", "event.id", "purchase.transaction", "transaction", "data.id", "data.purchase.transaction"])
    if val:
        return str(val)
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(f"{provider}:{raw}".encode("utf-8")).hexdigest()


def buyer_email(payload: dict) -> Optional[str]:
    val = deep_get(payload, [
        "buyer.email", "data.buyer.email", "purchase.buyer.email", "data.purchase.buyer.email",
        "subscriber.email", "customer.email", "client.email", "email", "user.email",
    ])
    return str(val).strip().lower() if val else None


def product_name(payload: dict) -> Optional[str]:
    val = deep_get(payload, [
        "product.name", "data.product.name", "purchase.product.name", "data.purchase.product.name",
        "offer.name", "data.offer.name", "product", "prod_name", "item.name",
    ])
    return str(val).strip() if val else None


def event_type(payload: dict) -> str:
    val = deep_get(payload, ["event", "event.type", "type", "status", "purchase.status", "data.status", "data.purchase.status"])
    return str(val or "unknown")


def purchase_status(payload: dict) -> str:
    val = deep_get(payload, ["purchase.status", "data.purchase.status", "status", "data.status", "event", "type"])
    return _lower(val)


def infer_plan(payload: dict) -> str:
    text = " ".join(str(x or "") for x in [product_name(payload), deep_get(payload, ["plan", "data.plan", "offer.name", "data.offer.name"])]).lower()
    if "performance" in text:
        return "performance"
    if "profissional" in text or "professional" in text:
        return "profissional"
    if "essencial" in text or "essential" in text or "basico" in text or "básico" in text:
        return "essencial"
    return plan_limits.normalize_plan(getattr(settings, "billing_default_plan", "profissional"))


def is_valid_token(provider: str, token: Optional[str]) -> bool:
    expected = settings.hotmart_webhook_token if provider == "hotmart" else settings.eduzz_webhook_token
    if not expected:
        return True  # permite teste/dev sem token, mas em produção recomenda-se configurar
    return bool(token) and token == expected


def process_billing_webhook(db: Session, provider: str, payload: dict) -> dict:
    provider = provider.lower().strip()
    ext_id = event_id(provider, payload)
    existing = db.query(BillingWebhookEvent).filter(
        BillingWebhookEvent.provider == provider,
        BillingWebhookEvent.external_event_id == ext_id,
    ).first()
    if existing and existing.status == "processed":
        return {"ok": True, "duplicate": True, "event_id": ext_id}

    email = buyer_email(payload)
    ev_type = event_type(payload)
    event = existing or BillingWebhookEvent(
        provider=provider,
        external_event_id=ext_id,
        event_type=ev_type,
        buyer_email=email,
        raw_payload=payload,
        status="received",
    )
    if existing is None:
        db.add(event)
        db.flush()

    if not email:
        event.status = "ignored"
        event.error = "buyer email ausente no payload"
        event.processed_at = datetime.now(timezone.utc)
        db.commit()
        return {"ok": False, "ignored": True, "reason": event.error, "event_id": ext_id}

    user = db.query(User).filter(User.email == email).first()
    if not user:
        event.status = "ignored"
        event.error = f"usuario nao encontrado para email {email}"
        event.processed_at = datetime.now(timezone.utc)
        db.commit()
        return {"ok": False, "ignored": True, "reason": event.error, "email": email, "event_id": ext_id}

    status = purchase_status(payload)
    plan = infer_plan(payload)
    active = status in ACTIVE_STATUSES or (not status or status == "unknown")
    inactive = status in INACTIVE_STATUSES

    sub = db.query(Subscription).filter(Subscription.owner_id == user.id, Subscription.provider == provider).first()
    if sub is None:
        sub = Subscription(owner_id=user.id, provider=provider)
        db.add(sub)
    sub.external_id = deep_get(payload, ["purchase.transaction", "transaction", "data.purchase.transaction", "id", "data.id"]) or ext_id
    sub.buyer_email = email
    sub.product_name = product_name(payload)
    sub.raw_payload = payload
    sub.plan = plan
    sub.updated_at = datetime.now(timezone.utc)

    if inactive:
        sub.status = "canceled" if status in {"canceled", "cancelled", "expired"} else status
        sub.canceled_at = datetime.now(timezone.utc)
        user.is_active = False
    elif active:
        sub.status = "active"
        sub.started_at = sub.started_at or datetime.now(timezone.utc)
        user.is_active = True
        user.plan = plan
        plan_limits.sync_ai_limit_for_user(db, user)
    else:
        sub.status = status or "received"

    event.status = "processed"
    event.error = None
    event.processed_at = datetime.now(timezone.utc)
    db.commit()
    return {"ok": True, "event_id": ext_id, "email": email, "user_id": user.id, "plan": user.plan, "active": user.is_active, "subscription_status": sub.status}
