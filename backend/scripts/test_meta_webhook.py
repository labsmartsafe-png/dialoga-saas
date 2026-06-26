"""
Teste local do webhook Meta (Fase 1) — NAO usa a Meta real.

Pre-requisitos (no terminal do servidor):
    $env:WHATSAPP_META_ENABLED = "true"
    $env:META_APP_SECRET = "dev_app_secret"   # precisa ser IGUAL ao SECRET abaixo
    uvicorn app.main:app --reload --port 8000

Rodar (em outro terminal, com a venv ativa):
    python scripts/test_meta_webhook.py

Prova 3 coisas:
  1) assinatura valida  -> 200
  2) reenvio identico   -> 200 (mas NAO duplica evento: dedup)
  3) assinatura invalida-> 403
"""
import hashlib
import hmac
import json

import httpx  # ja esta instalado no projeto

SECRET = "dev_app_secret"        # = META_APP_SECRET do servidor
URL = "http://localhost:8000/webhook/whatsapp/meta"

payload = {
    "object": "whatsapp_business_account",
    "entry": [{
        "id": "WABA",
        "changes": [{
            "field": "messages",
            "value": {
                "messaging_product": "whatsapp",
                "metadata": {"display_phone_number": "5511...", "phone_number_id": "PNID_TESTE"},
                "contacts": [{"profile": {"name": "Cliente"}, "wa_id": "5511988887777"}],
                "messages": [{
                    "from": "5511988887777",
                    "id": "wamid.ABC123",
                    "timestamp": "1780000000",
                    "type": "text",
                    "text": {"body": "ola 🚗"},
                }],
            },
        }],
    }],
}

# IMPORTANTE: postar EXATAMENTE estes bytes (assinatura e' sobre o corpo cru)
raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
sig = "sha256=" + hmac.new(SECRET.encode(), raw, hashlib.sha256).hexdigest()

with httpx.Client(timeout=15.0) as client:
    print("== 1) assinatura valida ==")
    r = client.post(URL, content=raw, headers={
        "Content-Type": "application/json", "X-Hub-Signature-256": sig})
    print("status:", r.status_code, "| esperado: 200")

    print("== 2) reenvio identico (dedup) ==")
    r = client.post(URL, content=raw, headers={
        "Content-Type": "application/json", "X-Hub-Signature-256": sig})
    print("status:", r.status_code, "| esperado: 200 (sem duplicar)")

    print("== 3) assinatura invalida ==")
    r = client.post(URL, content=raw, headers={
        "Content-Type": "application/json", "X-Hub-Signature-256": "sha256=deadbeef"})
    print("status:", r.status_code, "| esperado: 403")

print("\nPara conferir a dedup no banco (deve ser 1 evento, nao 2):")
print('  python -c "from app.database import SessionLocal; from app.models_whatsapp '
      'import WhatsAppInboundEvent as E; db=SessionLocal(); '
      "print('eventos:', db.query(E).count()); db.close()\"")
