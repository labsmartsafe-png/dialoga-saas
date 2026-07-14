"""
Conector de IA — abstraido, implementacao Gemini (Google AI Studio) via REST.

Por que REST (httpx) e nao SDK: zero dependencia nova pesada, e o httpx ja' esta no projeto.
Por que abstraido: trocar para OpenAI/outro depois e' so criar outra classe com a mesma interface.

Modelos (jun/2026):
- Embedding: gemini-embedding-001 (GA). Padrao 3072 dims; usamos 768 (sweet spot Google:
  ~mesma qualidade, 1/4 do armazenamento, abaixo do limite de indice do pgvector).
- Chat: gemini-2.0-flash (rapido e barato) — configuravel via settings.

Chave: GEMINI_API_KEY (Google AI Studio). Tolerante a ausencia: so falha quando chamado.
"""

import logging
from typing import Any

import httpx

from ..config import settings

logger = logging.getLogger("whatsflow.ai")

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"
EMBED_DIM = 768  # dimensao usada em todo o projeto (deve casar com o que esta salvo)


class AIProviderError(Exception):
    pass


class GeminiProvider:
    def __init__(self, api_key: str | None = None,
                 embed_model: str = "gemini-embedding-001",
                 chat_model: str | None = None):
        self.api_key = api_key or settings.gemini_api_key
        self.embed_model = embed_model
        self.chat_model = chat_model or settings.gemini_chat_model

    def _require_key(self):
        if not self.api_key:
            raise AIProviderError(
                "GEMINI_API_KEY nao configurada. Defina a env var para usar a IA."
            )

    # ---------------- Embeddings ----------------
    def embed(self, text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> list[float]:
        """Gera embedding de um texto. Retorna lista de floats (dimensao EMBED_DIM)."""
        self._require_key()
        url = f"{GEMINI_BASE}/models/{self.embed_model}:embedContent?key={self.api_key}"
        body = {
            "model": f"models/{self.embed_model}",
            "content": {"parts": [{"text": text}]},
            "taskType": task_type,
            "outputDimensionality": EMBED_DIM,
        }
        try:
            with httpx.Client(timeout=30.0) as client:
                r = client.post(url, json=body)
        except Exception as exc:
            raise AIProviderError(f"Erro de rede no embedding: {type(exc).__name__}") from exc
        if r.status_code != 200:
            raise AIProviderError(f"Embedding falhou HTTP {r.status_code}: {r.text[:300]}")
        data = r.json()
        values = (data.get("embedding") or {}).get("values")
        if not values:
            raise AIProviderError("Resposta de embedding sem 'values'.")
        return values

    # ---------------- Audio / Transcricao ----------------
    def transcribe_audio_base64(self, audio_base64: str, mime_type: str = "audio/mp4") -> str:
        """Transcreve áudio base64 usando Gemini multimodal.

        Retorna apenas o texto transcrito, em português do Brasil quando possível.
        """
        self._require_key()
        if not audio_base64:
            raise AIProviderError("Audio vazio para transcricao.")
        url = f"{GEMINI_BASE}/models/{self.chat_model}:generateContent?key={self.api_key}"
        body = {
            "contents": [{
                "role": "user",
                "parts": [
                    {"text": "Transcreva fielmente este áudio de WhatsApp para texto em português do Brasil. Responda somente com a transcrição, sem comentários."},
                    {"inline_data": {"mime_type": mime_type or "audio/mp4", "data": audio_base64}},
                ],
            }],
            "generationConfig": {"temperature": 0.0, "maxOutputTokens": 1200},
        }
        try:
            with httpx.Client(timeout=60.0) as client:
                r = client.post(url, json=body)
        except Exception as exc:
            raise AIProviderError(f"Erro de rede na transcricao: {type(exc).__name__}") from exc
        if r.status_code != 200:
            raise AIProviderError(f"Transcricao falhou HTTP {r.status_code}: {r.text[:300]}")
        data = r.json()
        try:
            cands = data.get("candidates") or []
            parts = (cands[0].get("content") or {}).get("parts") or []
            text = "".join(p.get("text", "") for p in parts).strip()
            return text or ""
        except Exception as exc:
            raise AIProviderError(f"Resposta de transcricao inesperada: {exc}") from exc

    # ---------------- Chat / Geracao ----------------
    def generate(self, system_prompt: str, user_message: str,
                 history: list[dict[str, Any]] | None = None,
                 temperature: float = 0.3) -> str:
        """
        Gera uma resposta de chat. history opcional: lista de {role, text}.
        role: 'user' | 'model'.
        """
        self._require_key()
        url = f"{GEMINI_BASE}/models/{self.chat_model}:generateContent?key={self.api_key}"
        contents = []
        for h in history or []:
            contents.append({"role": h.get("role", "user"),
                             "parts": [{"text": h.get("text", "")}]})
        contents.append({"role": "user", "parts": [{"text": user_message}]})

        body = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": contents,
            "generationConfig": {"temperature": temperature, "maxOutputTokens": 800},
        }
        try:
            with httpx.Client(timeout=40.0) as client:
                r = client.post(url, json=body)
        except Exception as exc:
            raise AIProviderError(f"Erro de rede na geracao: {type(exc).__name__}") from exc
        if r.status_code != 200:
            raise AIProviderError(f"Geracao falhou HTTP {r.status_code}: {r.text[:300]}")
        data = r.json()
        try:
            cands = data.get("candidates") or []
            parts = (cands[0].get("content") or {}).get("parts") or []
            text = "".join(p.get("text", "") for p in parts).strip()
            return text or ""
        except Exception as exc:
            raise AIProviderError(f"Resposta de geracao inesperada: {exc}") from exc


def get_ai_provider() -> GeminiProvider:
    """Factory — facilita trocar de provider no futuro."""
    return GeminiProvider()
