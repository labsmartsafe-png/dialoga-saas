"""
Fase E.3 — Webhooks de billing Hotmart/Eduzz.

Endpoints públicos para provedores de pagamento. Proteção por token simples:
- Authorization: Bearer <token>
- X-Hotmart-Hottok / X-Eduzz-Token
- ?token=<token>
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..services import billing_service

router = APIRouter()


def _extract_token(request: Request, token: str | None) -> str | None:
    if token:
        return token
    auth = request.headers.get("Authorization") or ""
    if auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    return (
        request.headers.get("X-Hotmart-Hottok")
        or request.headers.get("x-hotmart-hottok")
        or request.headers.get("X-Eduzz-Token")
        or request.headers.get("x-eduzz-token")
        or request.headers.get("X-Webhook-Token")
        or request.headers.get("x-webhook-token")
    )


async def _payload(request: Request) -> dict:
    try:
        data = await request.json()
        return data if isinstance(data, dict) else {"data": data}
    except Exception:
        form = await request.form()
        return dict(form)


@router.post("/hotmart/webhook")
async def hotmart_webhook(
    request: Request,
    token: str | None = Query(None),
    db: Session = Depends(get_db),
):
    received = _extract_token(request, token)
    if not billing_service.is_valid_token("hotmart", received):
        raise HTTPException(403, "Token de webhook Hotmart inválido.")
    data = await _payload(request)
    return billing_service.process_billing_webhook(db, "hotmart", data)


@router.post("/eduzz/webhook")
async def eduzz_webhook(
    request: Request,
    token: str | None = Query(None),
    db: Session = Depends(get_db),
):
    received = _extract_token(request, token)
    if not billing_service.is_valid_token("eduzz", received):
        raise HTTPException(403, "Token de webhook Eduzz inválido.")
    data = await _payload(request)
    return billing_service.process_billing_webhook(db, "eduzz", data)
