"""
Criptografia de segredos em repouso (tokens Meta, api keys Evolution).

Usa Fernet (cryptography) com suporte a ROTACAO de chave via MultiFernet.
- WA_FERNET_KEYS: uma ou mais chaves separadas por virgula. A PRIMEIRA encripta;
  todas conseguem decriptar (permite rotacionar sem reconectar clientes).
- Gerar chave:
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

IMPORTANTE:
- FACA BACKUP da chave. Perder a chave = perder todos os tokens (clientes reconectam).
- NUNCA logar o valor claro nem retornar token decriptado em respostas da API.

Tolerante a ausencia: se WA_FERNET_KEYS nao estiver setada, encrypt/decrypt levantam
RuntimeError SOMENTE quando chamados. Isso permite o app subir com a flag de WhatsApp
desligada sem exigir a chave.
"""

import os
from functools import lru_cache

from cryptography.fernet import Fernet, MultiFernet, InvalidToken


@lru_cache(maxsize=1)
def _get_fernet() -> MultiFernet:
    raw = os.environ.get("WA_FERNET_KEYS", "").strip()
    if not raw:
        raise RuntimeError(
            "WA_FERNET_KEYS nao configurada. Gere com Fernet.generate_key() e "
            "defina na env var (multiplas chaves separadas por virgula para rotacao)."
        )
    keys = [k.strip() for k in raw.split(",") if k.strip()]
    if not keys:
        raise RuntimeError("WA_FERNET_KEYS vazia apos parse.")
    try:
        fernets = [Fernet(k) for k in keys]
    except Exception as exc:  # chave mal formada
        raise RuntimeError(f"WA_FERNET_KEYS invalida: {exc}") from exc
    return MultiFernet(fernets)


def encrypt_secret(value: str | None) -> str | None:
    """Encripta uma string. Retorna texto base64 (cabe em coluna Text) ou None."""
    if value is None or value == "":
        return None
    return _get_fernet().encrypt(value.encode("utf-8")).decode("ascii")


def decrypt_secret(token: str | None) -> str | None:
    """Decripta. Retorna None se entrada vazia. Levanta ValueError se token invalido."""
    if token is None or token == "":
        return None
    try:
        return _get_fernet().decrypt(token.encode("ascii")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError(
            "Token criptografado invalido (chave Fernet errada/rotacionada incorretamente?)."
        ) from exc
