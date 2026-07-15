"""
Fase D.2.2 — Setup guiado em etapas.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import User
from ..services import niche_setup_service


router = APIRouter()


class SetupProfileRequest(BaseModel):
    package_id: str = Field(..., min_length=2, max_length=50)
    business_name: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = Field(None, max_length=500)
    hours: Optional[str] = Field(None, max_length=500)
    services: Optional[str] = Field(None, max_length=1000)
    human_contact: Optional[str] = Field(None, max_length=500)
    payment_methods: Optional[str] = Field(None, max_length=500)
    average_ticket: Optional[float] = Field(None, ge=0)
    extra_info: Optional[str] = Field(None, max_length=1500)


class CreateKbRequest(BaseModel):
    package_id: str = Field(..., min_length=2, max_length=50)
    business_name: Optional[str] = Field(None, max_length=255)
    text: str = Field(..., min_length=1, max_length=20000)


class IndexKbRequest(BaseModel):
    kb_id: int
    text: str = Field(..., min_length=1, max_length=20000)


@router.get("/niches")
def list_niches(current_user: User = Depends(get_current_user)):
    return niche_setup_service.list_packages()


@router.post("/create-flow")
def create_flow_step(
    payload: SetupProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        result = niche_setup_service.create_flow_from_package(
            db, current_user, payload.package_id, payload.business_name, payload.model_dump()
        )
        ticket = niche_setup_service.save_roi_if_present(db, current_user, payload.average_ticket)
        result["average_ticket_saved"] = ticket
        return result
    except KeyError:
        raise HTTPException(404, "Pacote de nicho não encontrado.")


@router.post("/create-kb")
def create_kb_step(
    payload: CreateKbRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return niche_setup_service.create_kb(db, current_user, payload.package_id, payload.business_name, payload.text)
    except KeyError:
        raise HTTPException(404, "Pacote de nicho não encontrado.")


@router.post("/index-kb")
def index_kb_step(
    payload: IndexKbRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return niche_setup_service.index_kb(db, current_user, payload.kb_id, payload.text)
    except KeyError:
        raise HTTPException(404, "Base de conhecimento não encontrada.")
    except Exception as exc:
        raise HTTPException(502, f"Falha ao ensinar IA: {exc}")


@router.post("/apply")
def apply_niche_package(
    payload: SetupProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Compatibilidade: cria fluxo e salva ROI, mas não indexa IA."""
    try:
        return niche_setup_service.apply_package(db, current_user, payload.package_id, payload.business_name, payload.model_dump())
    except KeyError:
        raise HTTPException(404, "Pacote de nicho não encontrado.")
