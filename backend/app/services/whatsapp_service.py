"""
Serviço de integração com WhatsApp Cloud API (Meta).

No MVP, funciona como cliente para envio de mensagens e validação do webhook.
"""
import logging
from typing import Optional, Dict, Any
import httpx

from ..config import settings

logger = logging.getLogger("whatsflow.whatsapp")


def send_text_message(to: str, text: str) -> Dict[str, Any]:
    """
    Envia mensagem de texto via WhatsApp Cloud API.
    Retorna dict com status e dados da resposta.
    """
    if not settings.whatsapp_token or not settings.whatsapp_phone_id:
        logger.warning("WhatsApp não configurado - mensagem não enviada.")
        return {
            "ok": False,
            "error": "WhatsApp não configurado. Defina WHATSAPP_TOKEN e WHATSAPP_PHONE_ID.",
        }
    url = f"{settings.whatsapp_api_url}/{settings.whatsapp_phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    try:
        with httpx.Client(timeout=15.0) as client:
            r = client.post(url, headers=headers, json=payload)
            return {
                "ok": r.status_code in (200, 201),
                "status_code": r.status_code,
                "response": r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text,
            }
    except Exception as e:
        logger.error("Erro ao enviar mensagem WhatsApp: %s", e)
        return {"ok": False, "error": str(e)}


def verify_webhook(mode: Optional[str], token: Optional[str], challenge: Optional[str]) -> Optional[str]:
    """
    Validação do webhook conforme Meta.
    Retorna o challenge se válido, caso contrário None.
    """
    if mode == "subscribe" and token == settings.whatsapp_verify_token:
        return challenge
    return None
