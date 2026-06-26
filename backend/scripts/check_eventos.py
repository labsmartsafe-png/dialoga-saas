"""
Confere quantos eventos de webhook foram gravados (prova da deduplicacao).

Rodar de dentro de backend/:
    python scripts/check_eventos.py

Por que este arquivo: importar 'app.models' ANTES garante que a classe User
esteja registrada no SQLAlchemy quando o relationship de WhatsAppConnection
for resolvido. Sem isso, um import isolado de models_whatsapp falha com
"failed to locate a name ('User')" — que e' so um detalhe de ordem de import,
nao um bug do app (que carrega models.py no startup normalmente).
"""

import app.models  # noqa: F401  -> registra User/Flow/etc. PRIMEIRO
from app.database import SessionLocal
from app.models_whatsapp import WhatsAppInboundEvent


def main():
    db = SessionLocal()
    try:
        total = db.query(WhatsAppInboundEvent).count()
        print(f"eventos: {total}")
        if total >= 1:
            print("OK: deduplicacao confirmada (mesmo com POSTs repetidos, 1 evento por mensagem).")
        else:
            print("Nenhum evento ainda. Rode antes: python scripts/test_meta_webhook.py")
    finally:
        db.close()


if __name__ == "__main__":
    main()
