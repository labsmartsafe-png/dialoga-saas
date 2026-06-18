"""
Rotas de templates - listagem e importação.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Template, Flow, User
from ..schemas import TemplateSummary, TemplateDetail, FlowOut
from ..auth import get_current_user

router = APIRouter()


def _to_summary(t: Template) -> TemplateSummary:
    nodes = t.flow_data if isinstance(t.flow_data, list) else []
    return TemplateSummary(
        slug=t.slug,
        name=t.name,
        description=t.description,
        category=t.category,
        icon=t.icon,
        node_count=len(nodes),
    )


@router.get("", response_model=list[TemplateSummary])
def list_templates(db: Session = Depends(get_db)):
    """Lista todos os templates disponíveis."""
    templates = db.query(Template).filter(Template.is_active == True).all()
    return [_to_summary(t) for t in templates]


@router.get("/{slug}", response_model=TemplateDetail)
def get_template(slug: str, db: Session = Depends(get_db)):
    """Detalhe completo de um template."""
    t = db.query(Template).filter(Template.slug == slug).first()
    if not t:
        raise HTTPException(404, "Template não encontrado")
    nodes = t.flow_data if isinstance(t.flow_data, list) else []
    return TemplateDetail(
        slug=t.slug,
        name=t.name,
        description=t.description,
        category=t.category,
        icon=t.icon,
        flow_data={"nodes": nodes},
    )


@router.post("/{slug}/import", response_model=FlowOut, status_code=201)
def import_template(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Importa um template como fluxo na conta do usuário."""
    t = db.query(Template).filter(Template.slug == slug).first()
    if not t:
        raise HTTPException(404, "Template não encontrado")
    nodes = t.flow_data if isinstance(t.flow_data, list) else []
    if not nodes:
        raise HTTPException(400, "Template sem nós definidos")
    start_id = nodes[0].get("id") if nodes else None

    flow = Flow(
        owner_id=current_user.id,
        name=f"{t.name} (importado)",
        description=t.description,
        nodes=nodes,
        start_node_id=start_id,
        active=True,
        template_slug=t.slug,
    )
    db.add(flow)
    db.commit()
    db.refresh(flow)
    return FlowOut.model_validate(flow)
