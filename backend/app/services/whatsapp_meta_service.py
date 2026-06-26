"""
Servico de ENVIO multi-tenant via Meta Cloud API.

Diferente do whatsapp_service.py legado (que usa token global das settings),
este envia usando o token CRIPTOGRAFADO de cada WhatsAppConnection.

Seguranca:
- decifra o token apenas em memoria, na hora do envio; nunca loga o token nem headers.
- mapeia erros comuns da Meta para mensagens uteis.

Sincrono (httpx.Client) para casar com o resto do projeto, que e' sync.
"""

import logging
from typing import Any, Dict

import httpx

from ..config import settings
from ..crypto import decrypt_secret

logger = logging.getLogger("whatsflow.whatsapp.meta_service")

# Mapa de erros conhecidos da Cloud API -> dica amigavel
_META_ERROR_HINTS = {
    190: "Token de acesso invalido ou expirado. Gere um novo token na Meta e reconecte.",
    131030: "Numero do destinatario nao esta na lista permitida (conta em modo de teste).",
    131047: "Fora da janela de 24h. Para iniciar conversa, use um template aprovado (HSM).",
    131056: "Limite de pares (remetente/destinatario) atingido. Tente novamente em instantes.",
    100: "Parametro invalido na requisicao (verifique phone_number_id e o numero destino).",
    133010: "Numero nao registrado na Cloud API.",
}


def _graph_url(phone_number_id: str) -> str:
    version = settings.meta_graph_version or "v23.0"
    return f"https://graph.facebook.com/{version}/{phone_number_id}/messages"


def send_text_via_connection(conn, to: str, text: str) -> Dict[str, Any]:
    """
    Envia texto livre por uma conexao Meta.
    Retorna dict padronizado: {ok, status_code, provider_message_id?, error?, error_code?, hint?}.
    NAO levanta excecao de rede (captura e retorna ok=False) para o chamador decidir.
    """
    if not conn or conn.provider != "meta":
        return {"ok": False, "error": "Conexao invalida ou nao e' do tipo Meta."}
    if not conn.phone_number_id:
        return {"ok": False, "error": "Conexao sem phone_number_id configurado."}

    try:
        token = decrypt_secret(conn.access_token_enc)
    except ValueError:
        return {"ok": False, "error": "Falha ao decifrar token (chave Fernet incorreta?)."}
    if not token:
        return {"ok": False, "error": "Conexao sem token configurado."}

    url = _graph_url(conn.phone_number_id)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": text},
    }

    try:
        with httpx.Client(timeout=20.0) as client:
            r = client.post(url, headers=headers, json=payload)
    except httpx.TimeoutException:
        logger.warning("Timeout ao enviar mensagem (conn=%s).", conn.id)
        return {"ok": False, "error": "Timeout ao contatar a Meta. A mensagem pode ou nao ter sido enviada."}
    except Exception as exc:  # nunca logar token; logar so o tipo
        logger.error("Erro de rede ao enviar (conn=%s): %s", conn.id, type(exc).__name__)
        return {"ok": False, "error": f"Erro de rede: {type(exc).__name__}"}

    # Resposta OK
    if r.status_code in (200, 201):
        data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        wamid = None
        try:
            wamid = (data.get("messages") or [{}])[0].get("id")
        except Exception:
            pass
        return {"ok": True, "status_code": r.status_code, "provider_message_id": wamid, "response": data}

    # Resposta de erro: extrair codigo da Meta
    err_code = None
    err_msg = f"HTTP {r.status_code}"
    try:
        body = r.json()
        meta_err = body.get("error", {}) or {}
        err_code = meta_err.get("code")
        err_msg = meta_err.get("message", err_msg)
    except Exception:
        err_msg = r.text[:300]

    hint = _META_ERROR_HINTS.get(err_code)
    logger.warning("Falha no envio (conn=%s) code=%s msg=%s", conn.id, err_code, err_msg)
    return {"ok": False, "status_code": r.status_code, "error": err_msg,
            "error_code": err_code, "hint": hint}


def validate_connection_token(access_token: str, phone_number_id: str) -> Dict[str, Any]:
    """
    Valida credenciais consultando o proprio phone number na Graph API (GET leve).
    Retorna {ok, display_phone_number?, verified_name?, error?, error_code?}.
    Usado ao salvar a conexao, para dar feedback imediato ao usuario.
    """
    version = settings.meta_graph_version or "v23.0"
    url = f"https://graph.facebook.com/{version}/{phone_number_id}"
    params = {"fields": "display_phone_number,verified_name,quality_rating"}
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        with httpx.Client(timeout=15.0) as client:
            r = client.get(url, headers=headers, params=params)
    except Exception as exc:
        return {"ok": False, "error": f"Erro de rede: {type(exc).__name__}"}

    if r.status_code == 200:
        d = r.json()
        return {"ok": True,
                "display_phone_number": d.get("display_phone_number"),
                "verified_name": d.get("verified_name")}
    try:
        meta_err = (r.json().get("error", {}) or {})
        code = meta_err.get("code")
        return {"ok": False, "error": meta_err.get("message", f"HTTP {r.status_code}"),
                "error_code": code, "hint": _META_ERROR_HINTS.get(code)}
    except Exception:
        return {"ok": False, "error": f"HTTP {r.status_code}"}
