"""
Rotas de dashboard - métricas agregadas.
"""
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models import Flow, Lead, Conversation, User
from ..schemas import DashboardMetrics
from ..auth import get_current_user

router = APIRouter()


@router.get("/metrics", response_model=DashboardMetrics)
def metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna métricas do dashboard do usuário."""
    flows_total = db.query(func.count(Flow.id)).filter(
        Flow.owner_id == current_user.id
    ).scalar() or 0
    flows_active = db.query(func.count(Flow.id)).filter(
        Flow.owner_id == current_user.id, Flow.active == True
    ).scalar() or 0
    leads_total = db.query(func.count(Lead.id)).filter(
        Lead.owner_id == current_user.id
    ).scalar() or 0
    today = datetime.now(timezone.utc).date()
    week_start = today - timedelta(days=today.weekday())
    leads_today = db.query(func.count(Lead.id)).filter(
        Lead.owner_id == current_user.id,
        func.date(Lead.created_at) == today,
    ).scalar() or 0
    leads_week = db.query(func.count(Lead.id)).filter(
        Lead.owner_id == current_user.id,
        Lead.created_at >= datetime.combine(week_start, datetime.min.time()),
    ).scalar() or 0
    conv_total = db.query(func.count(Conversation.id)).join(
        Flow, Flow.id == Conversation.flow_id
    ).filter(Flow.owner_id == current_user.id).scalar() or 0
    conv_sim = db.query(func.count(Conversation.id)).join(
        Flow, Flow.id == Conversation.flow_id
    ).filter(Flow.owner_id == current_user.id, Conversation.channel == "simulator").scalar() or 0
    conv_real = conv_total - conv_sim

    # Leads por dia (últimos 7 dias)
    leads_by_day = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = db.query(func.count(Lead.id)).filter(
            Lead.owner_id == current_user.id,
            func.date(Lead.created_at) == day,
        ).scalar() or 0
        leads_by_day.append({"date": day.isoformat(), "count": count})

    # Fluxos recentes
    recent_flows_q = (
        db.query(Flow)
        .filter(Flow.owner_id == current_user.id)
        .order_by(Flow.updated_at.desc())
        .limit(5)
        .all()
    )
    recent_flows = [
        {
            "id": f.id,
            "name": f.name,
            "active": f.active,
            "node_count": len(f.nodes or []),
            "updated_at": f.updated_at.isoformat() if f.updated_at else None,
        }
        for f in recent_flows_q
    ]

    # Leads recentes
    recent_leads_q = (
        db.query(Lead)
        .filter(Lead.owner_id == current_user.id)
        .order_by(Lead.created_at.desc())
        .limit(5)
        .all()
    )
    recent_leads = [
        {
            "id": l.id,
            "name": l.name,
            "phone": l.phone,
            "stage": l.stage,
            "status": l.status,
            "created_at": l.created_at.isoformat() if l.created_at else None,
        }
        for l in recent_leads_q
    ]

    return DashboardMetrics(
        flows_count=flows_total,
        active_flows_count=flows_active,
        leads_count=leads_total,
        leads_today=leads_today,
        leads_this_week=leads_week,
        conversations_total=conv_total,
        conversations_simulated=conv_sim,
        conversations_real=conv_real,
        leads_by_day=leads_by_day,
        recent_flows=recent_flows,
        recent_leads=recent_leads,
    )
