"""
Servico de RAG — indexa conteudo e responde perguntas com base nele.

Funciona em SQLite (dev) e Postgres (prod): a busca por similaridade e' feita em Python
(cosseno), entao nao depende de pgvector para funcionar. Em escala, dá pra migrar a busca
para pgvector sem mudar a interface deste servico.

Fluxo:
  index_text()  -> quebra em chunks -> gera embedding de cada -> salva
  answer()      -> embedding da pergunta -> busca top-k chunks -> monta prompt -> IA responde
"""

import logging
import math
import re
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..models_rag import KnowledgeBase, KnowledgeChunk, AISettings
from .ai_provider import get_ai_provider, AIProviderError

logger = logging.getLogger("whatsflow.rag")

CHUNK_SIZE = 800       # caracteres por chunk (aprox.)
CHUNK_OVERLAP = 120    # sobreposicao para nao cortar contexto no meio
TOP_K = 4              # quantos trechos recuperar por pergunta


# ----------------------------- Chunking -----------------------------
def split_into_chunks(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Quebra texto em pedacos, tentando respeitar quebras de paragrafo/frase."""
    text = re.sub(r"\n{3,}", "\n\n", (text or "").strip())
    if not text:
        return []
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + size, n)
        # tenta terminar em quebra de paragrafo/frase proxima
        if end < n:
            window = text[start:end]
            for sep in ("\n\n", ". ", "\n", " "):
                pos = window.rfind(sep)
                if pos > size * 0.5:
                    end = start + pos + len(sep)
                    break
        chunks.append(text[start:end].strip())
        start = max(end - overlap, end) if end <= start else end - overlap
        if start < 0:
            start = end
    return [c for c in chunks if c]


# ----------------------------- Similaridade -----------------------------
def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return -1.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return -1.0
    return dot / (na * nb)


# ----------------------------- Indexacao -----------------------------
def index_text(db: Session, kb: KnowledgeBase, text: str, source: str = "texto") -> int:
    """Indexa um texto na base: chunk -> embedding -> salva. Retorna nº de chunks criados."""
    provider = get_ai_provider()
    pieces = split_into_chunks(text)
    created = 0
    for i, piece in enumerate(pieces):
        try:
            emb = provider.embed(piece, task_type="RETRIEVAL_DOCUMENT")
        except AIProviderError as exc:
            logger.error("Falha ao gerar embedding (chunk %d): %s", i, exc)
            raise
        chunk = KnowledgeChunk(
            knowledge_base_id=kb.id,
            content=piece,
            source=source,
            chunk_index=i,
            embedding=emb,
            embedding_model=provider.embed_model,
            token_estimate=max(1, len(piece) // 4),
        )
        db.add(chunk)
        created += 1
    db.commit()
    return created


# ----------------------------- Busca -----------------------------
def search(db: Session, kb_id: int, query: str, top_k: int = TOP_K) -> list[KnowledgeChunk]:
    """Busca os chunks mais relevantes para a pergunta (cosseno em Python)."""
    provider = get_ai_provider()
    q_emb = provider.embed(query, task_type="RETRIEVAL_QUERY")
    chunks = (
        db.query(KnowledgeChunk)
        .filter(KnowledgeChunk.knowledge_base_id == kb_id)
        .all()
    )
    scored = []
    for c in chunks:
        if not c.embedding:
            continue
        scored.append((cosine_similarity(q_emb, c.embedding), c))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:top_k]]


# ----------------------------- Resposta (RAG) -----------------------------
def _build_system_prompt(ai: AISettings | None, context: str) -> str:
    persona = (ai.persona if ai and ai.persona else
               "Voce e' um atendente virtual prestativo de um negocio.")
    tone = (ai.tone if ai and ai.tone else "cordial")
    forbidden = (ai.forbidden_topics if ai and ai.forbidden_topics else [])
    fallback = (ai.fallback_message if ai and ai.fallback_message else
                "Vou te transferir para um atendente humano.")

    rules = [
        persona,
        f"Tom de voz: {tone}.",
        "Responda SOMENTE com base nas INFORMACOES fornecidas abaixo.",
        "Se a informacao nao estiver nas INFORMACOES, NAO invente: diga que vai transferir "
        f"para um humano usando exatamente esta frase: \"{fallback}\"",
        "Seja breve e direto, adequado para WhatsApp. Use no maximo 2-3 frases por resposta.",
    ]
    if forbidden:
        rules.append("Nunca fale sobre: " + ", ".join(forbidden) + ".")

    return (
        "\n".join(rules)
        + "\n\n===== INFORMACOES DO NEGOCIO =====\n"
        + (context if context.strip() else "(nenhuma informacao disponivel)")
        + "\n===== FIM DAS INFORMACOES =====\n"
    )


def _check_and_count_usage(db: Session, ai: AISettings) -> bool:
    """Controla limite mensal de IA. Retorna True se pode usar; incrementa o contador."""
    period = datetime.now(timezone.utc).strftime("%Y-%m")
    if ai.usage_period != period:
        ai.usage_period = period
        ai.monthly_ai_used = 0
    if ai.monthly_ai_limit and ai.monthly_ai_used >= ai.monthly_ai_limit:
        return False
    ai.monthly_ai_used = (ai.monthly_ai_used or 0) + 1
    db.commit()
    return True


def answer(db: Session, owner_id: int, kb_id: int, question: str,
           history: list[dict] | None = None) -> dict:
    """
    Responde uma pergunta usando RAG. Retorna:
      {ok, answer, used_chunks, transferred?(bool), error?}
    """
    ai = db.query(AISettings).filter(AISettings.owner_id == owner_id).first()
    if ai and not ai.enabled:
        return {"ok": False, "error": "IA desativada para este usuario."}

    # limite de uso
    if ai is not None and not _check_and_count_usage(db, ai):
        return {"ok": False, "error": "Limite mensal de IA atingido.",
                "transferred": True,
                "answer": (ai.fallback_message if ai else
                           "Vou te transferir para um atendente humano.")}

    try:
        top = search(db, kb_id, question)
    except AIProviderError as exc:
        return {"ok": False, "error": str(exc)}

    context = "\n\n---\n\n".join(c.content for c in top)
    system = _build_system_prompt(ai, context)

    try:
        text = get_ai_provider().generate(system, question, history=history)
    except AIProviderError as exc:
        return {"ok": False, "error": str(exc)}

    fallback = (ai.fallback_message if ai and ai.fallback_message else
                "Vou te transferir para um atendente humano.")
    transferred = fallback[:20].lower() in (text or "").lower()
    return {
        "ok": True,
        "answer": text,
        "used_chunks": len(top),
        "transferred": transferred,
    }
