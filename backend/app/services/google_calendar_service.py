"""
Serviço Google Calendar — Fase C.2.3.

Sem SDK externo: usa OAuth/Calendar REST com httpx.
Tokens ficam criptografados com o mesmo Fernet usado no WhatsApp.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urlencode

import httpx
from sqlalchemy.orm import Session

from ..config import settings
from ..crypto import decrypt_secret, encrypt_secret
from ..models import Appointment, CalendarConnection, Lead

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_CAL_BASE = "https://www.googleapis.com/calendar/v3"
SCOPES = "https://www.googleapis.com/auth/calendar.events"


def redirect_uri() -> str:
    return settings.google_redirect_uri or f"{(settings.public_base_url or '').rstrip('/')}/api/calendar/google/callback"


def is_configured() -> bool:
    return bool(settings.google_client_id and settings.google_client_secret)


def build_auth_url(state: str) -> str:
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": redirect_uri(),
        "response_type": "code",
        "scope": SCOPES,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
        "include_granted_scopes": "true",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def exchange_code(code: str) -> dict:
    body = {
        "code": code,
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "redirect_uri": redirect_uri(),
        "grant_type": "authorization_code",
    }
    with httpx.Client(timeout=30.0) as client:
        r = client.post(GOOGLE_TOKEN_URL, data=body)
    if r.status_code != 200:
        raise RuntimeError(f"Token Google falhou HTTP {r.status_code}: {r.text[:300]}")
    return r.json()


def get_connection(db: Session, owner_id: int) -> Optional[CalendarConnection]:
    return (
        db.query(CalendarConnection)
        .filter(CalendarConnection.owner_id == owner_id, CalendarConnection.provider == "google")
        .order_by(CalendarConnection.updated_at.desc())
        .first()
    )


def save_tokens(db: Session, owner_id: int, token_data: dict) -> CalendarConnection:
    conn = get_connection(db, owner_id)
    if conn is None:
        conn = CalendarConnection(owner_id=owner_id, provider="google", calendar_id="primary")
        db.add(conn)
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    expires_in = int(token_data.get("expires_in") or 3600)
    if access_token:
        conn.access_token_enc = encrypt_secret(access_token)
    if refresh_token:
        conn.refresh_token_enc = encrypt_secret(refresh_token)
    conn.token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=max(60, expires_in - 60))
    conn.status = "connected"
    conn.last_error = None
    conn.updated_at = datetime.now(timezone.utc)
    db.flush()
    return conn


def _refresh_access_token(db: Session, conn: CalendarConnection) -> str:
    refresh = decrypt_secret(conn.refresh_token_enc)
    if not refresh:
        raise RuntimeError("Conexão Google sem refresh_token. Reconecte o calendário.")
    body = {
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "refresh_token": refresh,
        "grant_type": "refresh_token",
    }
    with httpx.Client(timeout=30.0) as client:
        r = client.post(GOOGLE_TOKEN_URL, data=body)
    if r.status_code != 200:
        conn.status = "error"
        conn.last_error = r.text[:500]
        db.flush()
        raise RuntimeError(f"Refresh token Google falhou HTTP {r.status_code}: {r.text[:300]}")
    data = r.json()
    access = data.get("access_token")
    if not access:
        raise RuntimeError("Google não retornou access_token no refresh.")
    conn.access_token_enc = encrypt_secret(access)
    conn.token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(data.get("expires_in") or 3600) - 60)
    conn.status = "connected"
    conn.last_error = None
    db.flush()
    return access


def access_token(db: Session, conn: CalendarConnection) -> str:
    now = datetime.now(timezone.utc)
    if conn.access_token_enc and conn.token_expires_at and conn.token_expires_at > now:
        return decrypt_secret(conn.access_token_enc)
    return _refresh_access_token(db, conn)


def _event_body(db: Session, appt: Appointment) -> dict:
    lead = db.query(Lead).filter(Lead.id == appt.lead_id).first() if appt.lead_id else None
    start = appt.scheduled_at
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    end = start + timedelta(hours=1)
    desc_parts = []
    if lead:
        desc_parts.append(f"Lead: {lead.name or '-'}")
        desc_parts.append(f"Telefone: {lead.phone or '-'}")
    if appt.notes:
        desc_parts.append(f"Notas: {appt.notes}")
    desc_parts.append("Criado pelo dIAloga+")
    return {
        "summary": appt.title,
        "description": "\n".join(desc_parts),
        "start": {"dateTime": start.isoformat(), "timeZone": "America/Sao_Paulo"},
        "end": {"dateTime": end.isoformat(), "timeZone": "America/Sao_Paulo"},
    }


def sync_appointment(db: Session, owner_id: int, appt: Appointment) -> dict:
    """Cria/atualiza/cancela evento no Google Calendar.

    Retorna {ok, action, event_id?}. Não levanta para falhas de API; registra erro no appointment.
    """
    conn = get_connection(db, owner_id)
    if conn is None or conn.status != "connected":
        appt.calendar_sync_status = "disabled"
        appt.calendar_last_error = "Google Calendar não conectado."
        db.flush()
        return {"ok": False, "action": "disabled", "error": appt.calendar_last_error}
    try:
        token = access_token(db, conn)
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        calendar_id = conn.calendar_id or "primary"
        with httpx.Client(timeout=30.0) as client:
            if appt.status == "cancelado" and appt.external_event_id:
                url = f"{GOOGLE_CAL_BASE}/calendars/{calendar_id}/events/{appt.external_event_id}"
                r = client.delete(url, headers=headers)
                if r.status_code not in (200, 204, 410, 404):
                    raise RuntimeError(f"Delete evento Google HTTP {r.status_code}: {r.text[:300]}")
                appt.calendar_sync_status = "synced"
                appt.calendar_last_error = None
                db.flush()
                return {"ok": True, "action": "deleted", "event_id": appt.external_event_id}

            body = _event_body(db, appt)
            if appt.external_event_id:
                url = f"{GOOGLE_CAL_BASE}/calendars/{calendar_id}/events/{appt.external_event_id}"
                r = client.patch(url, headers=headers, json=body)
                action = "updated"
            else:
                url = f"{GOOGLE_CAL_BASE}/calendars/{calendar_id}/events"
                r = client.post(url, headers=headers, json=body)
                action = "created"
            if r.status_code not in (200, 201):
                raise RuntimeError(f"Sync evento Google HTTP {r.status_code}: {r.text[:300]}")
            data = r.json()
            appt.external_calendar_provider = "google"
            appt.external_event_id = data.get("id") or appt.external_event_id
            appt.calendar_sync_status = "synced"
            appt.calendar_last_error = None
            db.flush()
            return {"ok": True, "action": action, "event_id": appt.external_event_id}
    except Exception as exc:
        appt.calendar_sync_status = "error"
        appt.calendar_last_error = str(exc)[:500]
        db.flush()
        return {"ok": False, "action": "error", "error": appt.calendar_last_error}
