"""
Google Calendar OAuth + sincronização de agendamentos — Fase C.2.3.
"""
import base64
import hashlib
import hmac
import json
import time

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..config import settings
from ..database import SessionLocal, get_db
from ..models import Appointment, CalendarConnection, User
from ..services import google_calendar_service as gcal


router = APIRouter()


def _sign(payload: bytes) -> str:
    return hmac.new(settings.secret_key.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def _make_state(owner_id: int) -> str:
    payload = json.dumps({"owner_id": owner_id, "ts": int(time.time())}, separators=(",", ":")).encode("utf-8")
    b64 = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
    sig = _sign(b64.encode("ascii"))
    return f"{b64}.{sig}"


def _read_state(state: str) -> int:
    try:
        b64, sig = state.split(".", 1)
        if not hmac.compare_digest(_sign(b64.encode("ascii")), sig):
            raise ValueError("assinatura invalida")
        payload = base64.urlsafe_b64decode(b64 + "=" * (-len(b64) % 4))
        data = json.loads(payload.decode("utf-8"))
        if int(time.time()) - int(data.get("ts", 0)) > 15 * 60:
            raise ValueError("state expirado")
        return int(data["owner_id"])
    except Exception as exc:
        raise HTTPException(400, f"State OAuth invalido: {exc}")


@router.get("/google/auth-url")
def google_auth_url(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna URL para conectar Google Calendar."""
    if not settings.google_calendar_enabled:
        raise HTTPException(400, "Google Calendar nao esta habilitado.")
    if not gcal.is_configured():
        raise HTTPException(400, "GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET nao configurados.")
    return {"ok": True, "auth_url": gcal.build_auth_url(_make_state(current_user.id)), "redirect_uri": gcal.redirect_uri()}


@router.get("/google/callback")
def google_callback(
    code: str = Query(...),
    state: str = Query(...),
):
    """Callback público do Google OAuth.

    O usuário é identificado por um state assinado gerado em /auth-url.
    """
    owner_id = _read_state(state)
    db = SessionLocal()
    try:
        token_data = gcal.exchange_code(code)
        gcal.save_tokens(db, owner_id, token_data)
        db.commit()
        url = f"{settings.frontend_base_url.rstrip('/')}/configuracoes.html?calendar=connected"
        return RedirectResponse(url=url)
    except Exception as exc:
        db.rollback()
        url = f"{settings.frontend_base_url.rstrip('/')}/configuracoes.html?calendar=error"
        return RedirectResponse(url=url)
    finally:
        db.close()


@router.get("/status")
def calendar_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conn = gcal.get_connection(db, current_user.id)
    if not conn:
        return {"connected": False, "status": "disconnected", "provider": "google"}
    return {
        "connected": conn.status == "connected",
        "status": conn.status,
        "provider": conn.provider,
        "calendar_id": conn.calendar_id,
        "last_error": conn.last_error,
        "updated_at": conn.updated_at.isoformat() if conn.updated_at else None,
    }


@router.post("/disconnect")
def disconnect_calendar(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conn = gcal.get_connection(db, current_user.id)
    if conn:
        conn.status = "disconnected"
        conn.access_token_enc = None
        conn.refresh_token_enc = None
        db.commit()
    return {"ok": True}


@router.post("/sync-appointment/{appointment_id}")
def sync_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    appt = db.query(Appointment).filter(Appointment.id == appointment_id, Appointment.owner_id == current_user.id).first()
    if not appt:
        raise HTTPException(404, "Agendamento não encontrado.")
    result = gcal.sync_appointment(db, current_user.id, appt)
    db.commit()
    return result
