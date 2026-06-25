"""
Rotas de WhatsApp - envio de mensagens e webhook.
No MVP, o webhook está preparado para integração com a Meta Cloud API.
"""

from fastapi import APIRouter, Request, Query, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.whatsapp_service import send_text_message, verify_webhook
from ..schemas import WhatsAppSendText
from ..auth import get_current_user
from ..models import User

router = APIRouter()

# Webhook fica fora do prefixo /api/whatsapp para seguir padrão Meta
webhook_router = APIRouter()


@webhook_router.get("/webhook/whatsapp")
def webhook_verify(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """
    Verificação do webhook (Meta Cloud API).
    Responde com o challenge se o token estiver correto.
    """
    challenge = verify_webhook(hub_mode, hub_verify_token, hub_challenge)
    if challenge is None:
        raise HTTPException(403, "Token de verificação inválido.")
    return PlainTextResponse(content=challenge)


@webhook_router.post("/webhook/whatsapp")
async def webhook_receive(request: Request, db: Session = Depends(get_db)):
    """
    Recebe mensagens do WhatsApp.
    No MVP, apenas registra e responde 200 OK.
    Estrutura preparada para integração com motor de fluxo.
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    # Aqui entraria o processamento: identificar usuário, achar fluxo,
    # executar motor e responder via send_text_message.
    print(f"[WEBHOOK IN] {body}")
    return {"status": "received"}


@router.post("/send")
def send_message(
    payload: WhatsAppSendText,
    current_user: User = Depends(get_current_user),
):
    """Envia mensagem de texto via WhatsApp Cloud API."""
    result = send_text_message(payload.to, payload.text)
    if not result.get("ok"):
        raise HTTPException(502, f"Falha ao enviar: {result.get('error', 'desconhecido')}")
    return result