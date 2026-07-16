"""
Planos públicos/autenticados — Fase E.6.

Exibe planos, limites e URLs de checkout (Hotmart/Eduzz) quando configuradas.
"""
from fastapi import APIRouter, Depends

from ..auth import get_current_user
from ..config import settings
from ..models import User
from ..services import plan_limits

router = APIRouter()

PRICES = {
    "essencial": 147,
    "profissional": 297,
    "performance": 497,
}

DESCRIPTIONS = {
    "essencial": "Para começar com automação e CRM básico.",
    "profissional": "Para operação com mais fluxos, IA e atendimentos.",
    "performance": "Para negócios com maior volume e foco em ROI.",
}


def checkout_url(plan: str) -> str | None:
    provider = (settings.billing_provider or "manual").lower()
    if provider == "eduzz":
        return getattr(settings, f"eduzz_{plan}_url", "") or None
    return getattr(settings, f"hotmart_{plan}_url", "") or None


@router.get("")
def list_plans(current_user: User = Depends(get_current_user)):
    limits = plan_limits.public_plan_table()
    items = []
    for plan in ["essencial", "profissional", "performance"]:
        items.append({
            "id": plan,
            "name": plan.capitalize(),
            "price_brl": PRICES[plan],
            "description": DESCRIPTIONS[plan],
            "limits": limits[plan],
            "checkout_url": checkout_url(plan),
            "current": plan_limits.normalize_plan(current_user.plan) == plan,
        })
    return {"current_plan": plan_limits.normalize_plan(current_user.plan), "plans": items}
