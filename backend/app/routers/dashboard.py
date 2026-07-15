"""
Dashboard — métricas gerais e ROI operacional básico.

Mantém compatibilidade com o dashboard antigo e adiciona métricas úteis para venda:
- leads reais vs simulador
- atendimentos humanos pendentes
- agendamentos solicitados/confirmados/hoje/próximos 7 dias
- taxa de conversão lead real -> agendamento
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Appointment, Conversation, Flow, Lead, ROISettings, User
from ..services import lead_service
from ..schemas import ROISettingsOut, ROISettingsUpdate


router = APIRouter()


def _get_or_create_roi_settings(db: Session, owner_id: int) -> ROISettings:
    settings = db.query(ROISettings).filter(ROISettings.owner_id == owner_id).first()
    if settings is None:
        settings = ROISettings(owner_id=owner_id, average_ticket=0.0, currency="BRL")
        db.add(settings)
        db.flush()
    return settings


def _now():
    return datetime.now(timezone.utc)


def _start_of_day(dt: datetime) -> datetime:
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def _serialize_flow(flow: Flow) -> dict:
    return {
        "id": flow.id,
        "name": flow.name,
        "node_count": len(flow.nodes or []),
        "updated_at": flow.updated_at.isoformat() if flow.updated_at else None,
    }


def _serialize_lead(lead: Lead) -> dict:
    return {
        "id": lead.id,
        "name": lead.name,
        "phone": lead.phone,
        "status": lead.status,
        "source": lead.source,
        "created_at": lead.created_at.isoformat() if lead.created_at else None,
    }


@router.get("/roi-settings", response_model=ROISettingsOut)
def get_roi_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    settings = _get_or_create_roi_settings(db, current_user.id)
    db.commit()
    return ROISettingsOut.model_validate(settings)


@router.put("/roi-settings", response_model=ROISettingsOut)
def update_roi_settings(
    payload: ROISettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    settings = _get_or_create_roi_settings(db, current_user.id)
    settings.average_ticket = float(payload.average_ticket or 0)
    settings.currency = payload.currency or "BRL"
    settings.updated_at = _now()
    db.commit()
    db.refresh(settings)
    return ROISettingsOut.model_validate(settings)


@router.get("/metrics")
def metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = _now()
    today = _start_of_day(now)
    week_ago = now - timedelta(days=7)
    next_7 = now + timedelta(days=7)

    flows_q = db.query(Flow).filter(Flow.owner_id == current_user.id)
    leads_q = db.query(Lead).filter(Lead.owner_id == current_user.id)
    real_leads_q = leads_q.filter(Lead.source != "simulator")
    conv_q = db.query(Conversation).join(Flow, Flow.id == Conversation.flow_id).filter(Flow.owner_id == current_user.id)
    appt_q = db.query(Appointment).filter(Appointment.owner_id == current_user.id)

    leads_count = leads_q.count()
    real_leads_count = real_leads_q.count()
    simulator_leads_count = leads_q.filter(Lead.source == "simulator").count()

    appointments_total = appt_q.count()
    appointments_requested = appt_q.filter(Appointment.status == "solicitado").count()
    appointments_confirmed = appt_q.filter(Appointment.status == "confirmado").count()
    appointments_done = appt_q.filter(Appointment.status == "realizado").count()
    appointments_today = appt_q.filter(Appointment.scheduled_at >= today, Appointment.scheduled_at < today + timedelta(days=1)).count()
    appointments_next_7_days = appt_q.filter(Appointment.scheduled_at >= now, Appointment.scheduled_at <= next_7).count()

    roi_settings = _get_or_create_roi_settings(db, current_user.id)
    average_ticket = float(roi_settings.average_ticket or 0)
    estimated_confirmed_revenue = round(appointments_confirmed * average_ticket, 2)
    estimated_done_revenue = round(appointments_done * average_ticket, 2)
    estimated_pipeline_revenue = round((appointments_requested + appointments_confirmed) * average_ticket, 2)

    human_pending = leads_q.filter(Lead.status == lead_service.STATUS_AGUARDANDO_HUMANO).count()
    human_active = leads_q.filter(Lead.status == lead_service.STATUS_EM_ATENDIMENTO_HUMANO).count()

    # Conversão operacional simples: leads reais que têm ao menos um agendamento / total leads reais.
    lead_ids_with_appt = {
        row[0]
        for row in db.query(Appointment.lead_id)
        .filter(Appointment.owner_id == current_user.id, Appointment.lead_id.isnot(None))
        .distinct()
        .all()
    }
    real_lead_ids = {row[0] for row in real_leads_q.with_entities(Lead.id).all()}
    real_leads_with_appointment = len(real_lead_ids.intersection(lead_ids_with_appt))
    appointment_conversion_rate = round((real_leads_with_appointment / real_leads_count) * 100, 1) if real_leads_count else 0.0

    # Leads por dia (últimos 7 dias)
    leads_by_day = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        nxt = day + timedelta(days=1)
        count = leads_q.filter(Lead.created_at >= day, Lead.created_at < nxt).count()
        leads_by_day.append({"date": day.date().isoformat(), "count": count})

    recent_flows = flows_q.order_by(Flow.updated_at.desc()).limit(5).all()
    recent_leads = leads_q.order_by(Lead.created_at.desc()).limit(5).all()

    return {
        # Compatibilidade com dashboard antigo
        "flows_count": flows_q.count(),
        "active_flows_count": flows_q.filter(Flow.active == True).count(),  # noqa: E712
        "leads_count": leads_count,
        "leads_today": leads_q.filter(Lead.created_at >= today).count(),
        "leads_this_week": leads_q.filter(Lead.created_at >= week_ago).count(),
        "conversations_total": conv_q.count(),
        "conversations_simulated": conv_q.filter(Conversation.channel == "simulator").count(),
        "conversations_real": conv_q.filter(Conversation.channel != "simulator").count(),
        "leads_by_day": leads_by_day,
        "recent_flows": [_serialize_flow(f) for f in recent_flows],
        "recent_leads": [_serialize_lead(l) for l in recent_leads],

        # Novas métricas ROI/CRM
        "real_leads_count": real_leads_count,
        "simulator_leads_count": simulator_leads_count,
        "human_pending_count": human_pending,
        "human_active_count": human_active,
        "appointments_total": appointments_total,
        "appointments_requested": appointments_requested,
        "appointments_confirmed": appointments_confirmed,
        "appointments_done": appointments_done,
        "appointments_today": appointments_today,
        "appointments_next_7_days": appointments_next_7_days,
        "real_leads_with_appointment": real_leads_with_appointment,
        "appointment_conversion_rate": appointment_conversion_rate,
        "roi_average_ticket": average_ticket,
        "roi_currency": roi_settings.currency or "BRL",
        "estimated_confirmed_revenue": estimated_confirmed_revenue,
        "estimated_done_revenue": estimated_done_revenue,
        "estimated_pipeline_revenue": estimated_pipeline_revenue,
    }
