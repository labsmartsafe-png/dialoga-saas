"""
Fase D.1 — Setup/Pacotes por nicho.
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


class ApplyPackageRequest(BaseModel):
    package_id: str = Field(..., min_length=2, max_length=50)
    business_name: Optional[str] = Field(None, max_length=255)


@router.get("/niches")
def list_niches(
    current_user: User = Depends(get_current_user),
):
    """Lista pacotes de nicho disponíveis."""
    return niche_setup_service.list_packages()


@router.post("/apply")
def apply_niche_package(
    payload: ApplyPackageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Aplica pacote criando um fluxo pronto e retornando orientações."""
    try:
        return niche_setup_service.apply_package(db, current_user, payload.package_id, payload.business_name)
    except KeyError:
        raise HTTPException(404, "Pacote de nicho não encontrado.")
