"""
Rotas de leads - CRM 1.0.

Inclui filtros por origem para separar:
- simulator
- whatsapp_evolution
- whatsapp_meta
- manual/import/api no futuro
"""
import csv
import io
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Conversation, Flow, Lead, User
from ..schemas import LeadOut, LeadUpdate


router = APIRouter()


def _parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise HTTPException(400, "Datas devem estar em ISO 8601 (YYYY-MM-DD).")


@router.get("", response_model=list[LeadOut])
def list_leads(
    flow_id: Optional[int] = None,
    status: Optional[str] = None,
    source: Optional[str] = None,
    include_simulator: bool = True,
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
    if source:
        q = q.filter(Lead.source == source)
    elif include_simulator is False:
        q = q.filter(Lead.source != "simulator")

    dt_from = _parse_date(date_from)
    dt_to = _parse_date(date_to)
    if dt_from:
        q = q.filter(Lead.created_at >= dt_from)
    if dt_to:
        q = q.filter(Lead.created_at <= dt_to)

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
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.owner_id == current_user.id).first()
    if not lead:
        raise HTTPException(404, "Lead não encontrado")

    if payload.name is not None:
        lead.name = payload.name
    if payload.status is not None:
        lead.status = payload.status
    if payload.stage is not None:
        lead.stage = payload.stage
    if hasattr(lead, "updated_at"):
        lead.updated_at = datetime.now(timezone.utc)

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
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.owner_id == current_user.id).first()
    if not lead:
        raise HTTPException(404, "Lead não encontrado")

    # CRM 1.0+: conversas podem apontar para leads via conversations.lead_id.
    # Se apagarmos o lead sem limpar esse vínculo, o PostgreSQL pode bloquear o DELETE
    # por chave estrangeira. Preservamos o histórico da conversa e apenas desvinculamos.
    db.query(Conversation).filter(
        Conversation.lead_id == lead.id
    ).update({Conversation.lead_id: None}, synchronize_session=False)

    db.delete(lead)
    db.commit()
    return


@router.get("/export/csv")
def export_leads_csv(
    flow_id: Optional[int] = None,
    source: Optional[str] = None,
    include_simulator: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Exporta leads em CSV, incluindo variáveis do contexto."""
    q = db.query(Lead).filter(Lead.owner_id == current_user.id)
    if flow_id:
        q = q.filter(Lead.flow_id == flow_id)
    if source:
        q = q.filter(Lead.source == source)
    elif include_simulator is False:
        q = q.filter(Lead.source != "simulator")

    leads = q.order_by(Lead.created_at.desc()).all()
    flows_map = {f.id: f.name for f in db.query(Flow).filter(Flow.owner_id == current_user.id).all()}

    all_context_keys = set()
    for l in leads:
        ctx = l.context if isinstance(l.context, dict) else {}
        all_context_keys.update(ctx.keys())
    context_keys = sorted(all_context_keys)

    output = io.StringIO()
    output.write("\ufeff")
    writer = csv.writer(output)

    header = [
        "id", "nome", "telefone", "email", "fluxo", "status", "etapa", "origem",
        "conversation_id", "connection_id", "ultima_interacao", "data_criacao",
    ]
    header += context_keys
    writer.writerow(header)

    for l in leads:
        ctx = l.context if isinstance(l.context, dict) else {}
        row = [
            l.id,
            l.name or "",
            l.phone or "",
            l.email or "",
            flows_map.get(l.flow_id, ""),
            l.status or "",
            l.stage or "",
            l.source or "",
            getattr(l, "conversation_id", None) or "",
            getattr(l, "connection_id", None) or "",
            l.last_interaction_at.isoformat() if getattr(l, "last_interaction_at", None) else "",
            l.created_at.isoformat() if l.created_at else "",
        ]
        for key in context_keys:
            row.append(ctx.get(key, ""))
        writer.writerow(row)

    output.seek(0)
    filename = f"leads-dialoga-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
