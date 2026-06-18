"""
Rotas de leads - listagem, filtros e exportação CSV.
"""
import csv
import io
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models import Lead, Flow, User
from ..schemas import LeadOut, LeadUpdate
from ..auth import get_current_user

router = APIRouter()


@router.get("", response_model=list[LeadOut])
def list_leads(
    flow_id: Optional[int] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista leads com filtros opcionais."""
    q = db.query(Lead).filter(Lead.owner_id == current_user.id)
    if flow_id:
        q = q.filter(Lead.flow_id == flow_id)
    if status:
        q = q.filter(Lead.status == status)
    try:
        if date_from:
            q = q.filter(Lead.created_at >= datetime.fromisoformat(date_from))
        if date_to:
            q = q.filter(Lead.created_at <= datetime.fromisoformat(date_to))
    except ValueError:
        raise HTTPException(400, "Datas devem estar em ISO 8601 (YYYY-MM-DD).")
    leads = q.order_by(Lead.created_at.desc()).all()
    return [LeadOut.model_validate(l) for l in leads]


@router.put("/{lead_id}", response_model=LeadOut)
def update_lead(
    lead_id: int,
    payload: LeadUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Atualiza dados do lead."""
    lead = db.query(Lead).filter(
        Lead.id == lead_id, Lead.owner_id == current_user.id
    ).first()
    if not lead:
        raise HTTPException(404, "Lead não encontrado")
    if payload.name is not None:
        lead.name = payload.name
    if payload.status is not None:
        lead.status = payload.status
    db.commit()
    db.refresh(lead)
    return LeadOut.model_validate(lead)


@router.delete("/{lead_id}", status_code=204)
def delete_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Exclui um lead."""
    lead = db.query(Lead).filter(
        Lead.id == lead_id, Lead.owner_id == current_user.id
    ).first()
    if not lead:
        raise HTTPException(404, "Lead não encontrado")
    db.delete(lead)
    db.commit()
    return


@router.get("/export/csv")
def export_leads_csv(
    flow_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Exporta os leads filtrados em CSV."""
    q = db.query(Lead).filter(Lead.owner_id == current_user.id)
    if flow_id:
        q = q.filter(Lead.flow_id == flow_id)
    leads = q.order_by(Lead.created_at.desc()).all()
    flows_map = {f.id: f.name for f in db.query(Flow).filter(Flow.owner_id == current_user.id).all()}

    output = io.StringIO()
    # BOM para Excel reconhecer UTF-8
    output.write("\ufeff")
    writer = csv.writer(output)
    writer.writerow([
        "id", "nome", "telefone", "email", "fluxo", "etapa", "status",
        "origem", "data_criacao",
    ])
    for l in leads:
        writer.writerow([
            l.id,
            l.name or "",
            l.phone or "",
            l.email or "",
            flows_map.get(l.flow_id, ""),
            l.stage or "",
            l.status or "",
            l.source or "",
            l.created_at.isoformat() if l.created_at else "",
        ])
    output.seek(0)
    filename = f"leads-whatsflow-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
