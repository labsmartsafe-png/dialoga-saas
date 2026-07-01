"""
Router da Fase A — IA + RAG.
Montado em /api/ai. Segue o padrao: Depends(get_db) + Depends(get_current_user),
filtros por owner_id, respostas com model_validate.

Endpoints:
  POST   /api/ai/knowledge-bases                cria base de conhecimento
  GET    /api/ai/knowledge-bases                lista bases do usuario
  DELETE /api/ai/knowledge-bases/{id}           remove base
  POST   /api/ai/knowledge-bases/{id}/index     indexa um texto na base (gera embeddings)
  GET    /api/ai/settings                        le config de IA do usuario (cria default)
  PUT    /api/ai/settings                        atualiza config de IA
  POST   /api/ai/ask                             pergunta -> resposta via RAG (teste/simulador)
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..models_rag import KnowledgeBase, KnowledgeChunk, AISettings
from ..schemas_rag import (
    KnowledgeBaseCreate, KnowledgeBaseOut, IndexTextRequest,
    AISettingsUpdate, AISettingsOut, AIAskRequest,
)
from ..auth import get_current_user
from ..services import rag_service

logger = logging.getLogger("whatsflow.router.ai")

router = APIRouter()


def _get_owned_kb(db: Session, kb_id: int, user: User) -> KnowledgeBase:
    kb = (
        db.query(KnowledgeBase)
        .filter(KnowledgeBase.id == kb_id, KnowledgeBase.owner_id == user.id)
        .first()
    )
    if not kb:
        raise HTTPException(404, "Base de conhecimento nao encontrada.")
    return kb


# ---------------- Knowledge Bases ----------------
@router.post("/knowledge-bases", response_model=KnowledgeBaseOut)
def create_kb(payload: KnowledgeBaseCreate, db: Session = Depends(get_db),
              current_user: User = Depends(get_current_user)):
    kb = KnowledgeBase(owner_id=current_user.id, name=payload.name,
                       description=payload.description)
    db.add(kb)
    db.commit()
    db.refresh(kb)
    return KnowledgeBaseOut.model_validate(kb)


@router.get("/knowledge-bases", response_model=list[KnowledgeBaseOut])
def list_kb(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    kbs = (
        db.query(KnowledgeBase)
        .filter(KnowledgeBase.owner_id == current_user.id)
        .order_by(KnowledgeBase.created_at.desc())
        .all()
    )
    return [KnowledgeBaseOut.model_validate(k) for k in kbs]


@router.delete("/knowledge-bases/{kb_id}", status_code=204)
def delete_kb(kb_id: int, db: Session = Depends(get_db),
              current_user: User = Depends(get_current_user)):
    kb = _get_owned_kb(db, kb_id, current_user)
    db.delete(kb)
    db.commit()
    return


@router.post("/knowledge-bases/{kb_id}/index")
def index_kb(kb_id: int, payload: IndexTextRequest, db: Session = Depends(get_db),
             current_user: User = Depends(get_current_user)):
    kb = _get_owned_kb(db, kb_id, current_user)
    try:
        created = rag_service.index_text(db, kb, payload.text, source=payload.source or "texto")
    except Exception as exc:
        raise HTTPException(502, f"Falha ao indexar: {exc}")
    total = db.query(KnowledgeChunk).filter(KnowledgeChunk.knowledge_base_id == kb.id).count()
    return {"ok": True, "chunks_created": created, "chunks_total": total}


# ---------------- AI Settings ----------------
def _get_or_create_settings(db: Session, user: User) -> AISettings:
    ai = db.query(AISettings).filter(AISettings.owner_id == user.id).first()
    if ai is None:
        ai = AISettings(owner_id=user.id)
        db.add(ai)
        db.commit()
        db.refresh(ai)
    return ai


@router.get("/settings", response_model=AISettingsOut)
def get_settings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return AISettingsOut.model_validate(_get_or_create_settings(db, current_user))


@router.put("/settings", response_model=AISettingsOut)
def update_settings(payload: AISettingsUpdate, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    ai = _get_or_create_settings(db, current_user)
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(ai, k, v)
    db.commit()
    db.refresh(ai)
    return AISettingsOut.model_validate(ai)


# ---------------- Ask (RAG) ----------------
@router.post("/ask")
def ask(payload: AIAskRequest, db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    # garante que a base e' do usuario
    _get_owned_kb(db, payload.knowledge_base_id, current_user)
    result = rag_service.answer(db, current_user.id, payload.knowledge_base_id, payload.question)
    if not result.get("ok"):
        raise HTTPException(502, result.get("error", "Falha na IA."))
    return result
