"""
Rotas de fluxos - CRUD completo e simulação.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import Flow, User, Conversation
from ..schemas import (
    FlowCreate, FlowUpdate, FlowOut,
    SimulatorStart, SimulatorMessage, SimulatorResponse,
)
from ..auth import get_current_user
from ..services.flow_engine import (
    start_conversation, send_user_message, serialize_conversation,
    get_current_node_view,
)

router = APIRouter()


@router.get("", response_model=list[FlowOut])
def list_flows(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lista todos os fluxos do usuário."""
    flows = (
        db.query(Flow)
        .filter(Flow.owner_id == current_user.id)
        .order_by(Flow.updated_at.desc())
        .all()
    )
    return [FlowOut.model_validate(f) for f in flows]


@router.post("", response_model=FlowOut, status_code=201)
def create_flow(
    payload: FlowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cria um novo fluxo."""
    nodes = [n.model_dump() for n in payload.nodes]
    start_id = payload.start_node_id
    if not start_id and nodes:
        start_id = nodes[0].get("id")
    flow = Flow(
        owner_id=current_user.id,
        name=payload.name,
        description=payload.description,
        nodes=nodes,
        start_node_id=start_id,
        active=True,
        template_slug=payload.template_slug,
        mode=payload.mode or "guided",
    )
    db.add(flow)
    db.commit()
    db.refresh(flow)
    return FlowOut.model_validate(flow)


@router.get("/{flow_id}", response_model=FlowOut)
def get_flow(
    flow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Detalhe de um fluxo."""
    flow = db.query(Flow).filter(
        Flow.id == flow_id, Flow.owner_id == current_user.id
    ).first()
    if not flow:
        raise HTTPException(404, "Fluxo não encontrado")
    return FlowOut.model_validate(flow)


@router.put("/{flow_id}", response_model=FlowOut)
def update_flow(
    flow_id: int,
    payload: FlowUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Atualiza um fluxo."""
    flow = db.query(Flow).filter(
        Flow.id == flow_id, Flow.owner_id == current_user.id
    ).first()
    if not flow:
        raise HTTPException(404, "Fluxo não encontrado")
    data = payload.model_dump(exclude_unset=True)
    if "nodes" in data and data["nodes"] is not None:
        flow.nodes = [n if isinstance(n, dict) else n for n in data["nodes"]]
    if "name" in data:
        flow.name = data["name"]
    if "description" in data:
        flow.description = data["description"]
    if "start_node_id" in data:
        flow.start_node_id = data["start_node_id"]
    if "active" in data:
        flow.active = data["active"]
    if "mode" in data and data["mode"]:
        flow.mode = data["mode"]
    db.commit()
    db.refresh(flow)
    return FlowOut.model_validate(flow)


@router.delete("/{flow_id}", status_code=204)
def delete_flow(
    flow_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Exclui um fluxo."""
    flow = db.query(Flow).filter(
        Flow.id == flow_id, Flow.owner_id == current_user.id
    ).first()
    if not flow:
        raise HTTPException(404, "Fluxo não encontrado")
    db.delete(flow)
    db.commit()
    return


# =============== SIMULADOR ===============
@router.post("/{flow_id}/simulate/start", response_model=SimulatorResponse)
def simulate_start(
    flow_id: int,
    payload: SimulatorStart = SimulatorStart(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Inicia uma simulação para o fluxo."""
    flow = db.query(Flow).filter(
        Flow.id == flow_id, Flow.owner_id == current_user.id
    ).first()
    if not flow:
        raise HTTPException(404, "Fluxo não encontrado")
    try:
        conv = start_conversation(
            db, flow, payload.user_name or "Visitante", payload.user_phone
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    data = serialize_conversation(db, conv)
    node, opts = get_current_node_view(db, conv, flow)
    return SimulatorResponse(
        conversation_id=conv.id,
        finished=conv.is_active is False,
        current_node=node,
        bot_message=(node or {}).get("content"),
        options=opts,
        awaiting_input=node is not None and node.get("type") in ("question", "input"),
        context=data["context"],
        messages=data["messages"],
    )


@router.post("/simulate/message", response_model=SimulatorResponse)
def simulate_message(
    payload: SimulatorMessage,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Envia resposta do usuário na simulação."""
    conv = db.query(Conversation).filter(Conversation.id == payload.conversation_id).first()
    if not conv:
        raise HTTPException(404, "Conversa não encontrada")
    flow = db.query(Flow).filter(Flow.id == conv.flow_id).first()
    if not flow or flow.owner_id != current_user.id:
        raise HTTPException(403, "Acesso negado")
    send_user_message(db, conv, flow, text=payload.text, selected_option=payload.selected_option)
    data = serialize_conversation(db, conv)
    node, opts = get_current_node_view(db, conv, flow)
    return SimulatorResponse(
        conversation_id=conv.id,
        finished=conv.is_active is False,
        current_node=node,
        bot_message=(node or {}).get("content"),
        options=opts,
        awaiting_input=node is not None and node.get("type") in ("question", "input"),
        context=data["context"],
        messages=data["messages"],
    )
