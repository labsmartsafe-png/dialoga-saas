"""
Testes básicos do dIAloga+.
Cobre:
- Health check
- Registro e login
- Listagem de templates (após seed)
- Importação de template
- CRUD de fluxo
- Simulação completa (verifica se cria lead ao final)
"""

import os
import sys

import pytest
from fastapi.testclient import TestClient

# Garante que o diretório backend está no path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))

# Usa SQLite para testes
os.environ["DATABASE_URL"] = "sqlite:///./data/test_dialoga.db"
os.environ["SECRET_KEY"] = "test-secret-key-test-secret-key-test-secret-key-test-1234"
os.environ["WHATSAPP_VERIFY_TOKEN"] = "dialoga-verify"

from app.main import app  # noqa: E402
from app.database import Base, engine  # noqa: E402
from app.services.template_loader import seed_templates  # noqa: E402
from app.database import SessionLocal  # noqa: E402

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    """Cria tabelas e popula templates antes dos testes."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        count = seed_templates(db)
        print(f"\n[TEST SETUP] {count} templates carregados")
    finally:
        db.close()


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert "dIAloga" in r.json()["app"]


def test_register_login_me():
    email = f"teste_{os.urandom(3).hex()}@dialoga.com"
    r = client.post("/api/auth/register", json={
        "email": email,
        "password": "123456",
        "company_name": "Empresa Teste",
        "full_name": "Usuário Teste",
    })
    assert r.status_code == 201, r.text
    token = r.json()["access_token"]
    assert token

    # Login
    r2 = client.post("/api/auth/login", json={"email": email, "password": "123456"})
    assert r2.status_code == 200
    assert r2.json()["access_token"]

    # Me
    r3 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r3.status_code == 200
    assert r3.json()["email"] == email


def test_register_duplicate_email():
    email = f"dup_{os.urandom(3).hex()}@dialoga.com"
    client.post("/api/auth/register", json={
        "email": email,
        "password": "123456",
        "company_name": "Empresa A",
    })
    r = client.post("/api/auth/register", json={
        "email": email,
        "password": "123456",
        "company_name": "Empresa B",
    })
    assert r.status_code == 400


def test_login_wrong_password():
    r = client.post("/api/auth/login", json={
        "email": "naoexiste@dialoga.com",
        "password": "errada",
    })
    assert r.status_code == 401


def test_list_templates():
    r = client.get("/api/templates")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 8  # 8 templates
    slugs = {t["slug"] for t in data}
    for expected in ["veiculos", "clinica", "imobiliaria", "restaurante", "academias", "salao-beleza", "petshop", "e-commerce"]:
        assert expected in slugs, f"Template '{expected}' não encontrado."


def test_import_template_and_simulate():
    # Cria usuário único
    email = f"sim_{os.urandom(3).hex()}@dialoga.com"
    r = client.post("/api/auth/register", json={
        "email": email,
        "password": "123456",
        "company_name": "Empresa Sim",
    })
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Importar template
    r2 = client.post("/api/templates/veiculos/import", headers=headers)
    assert r2.status_code == 201, r2.text
    flow_id = r2.json()["id"]
    assert r2.json()["nodes"]

    # Iniciar simulação
    r3 = client.post(f"/api/flows/{flow_id}/simulate/start", headers=headers, json={
        "user_name": "Visitante Teste"
    })
    assert r3.status_code == 200
    conv_id = r3.json()["conversation_id"]
    assert r3.json()["context"].get("nome") == "Visitante Teste"

    # Enviar opção "carro"
    r4 = client.post("/api/flows/simulate/message", headers=headers, json={
        "conversation_id": conv_id,
        "selected_option": "carro",
    })
    assert r4.status_code == 200
    assert r4.json()["context"].get("interesse") == "carro"

    # Continua simulando até o fim para verificar criação de lead
    r5 = client.post("/api/flows/simulate/message", headers=headers, json={
        "conversation_id": conv_id,
        "selected_option": "suv",
    })
    assert r5.status_code == 200
    assert r5.json()["context"].get("tipo_veiculo") == "suv"

    r6 = client.post("/api/flows/simulate/message", headers=headers, json={
        "conversation_id": conv_id,
        "selected_option": "ate_40k",
    })
    assert r6.status_code == 200

    r7 = client.post("/api/flows/simulate/message", headers=headers, json={
        "conversation_id": conv_id,
        "text": "João da Silva",
    })
    assert r7.status_code == 200
    assert r7.json()["context"].get("nome") == "João da Silva"

    r8 = client.post("/api/flows/simulate/message", headers=headers, json={
        "conversation_id": conv_id,
        "text": "(11) 98888-7777",
    })
    assert r8.status_code == 200

    # Verifica leads
    r9 = client.get("/api/leads", headers=headers)
    assert r9.status_code == 200
    leads = r9.json()
    assert len(leads) >= 1, "Esperava pelo menos 1 lead capturado"


def test_create_flow_update_delete():
    email = f"flow_{os.urandom(3).hex()}@dialoga.com"
    client.post("/api/auth/register", json={
        "email": email,
        "password": "123456",
        "company_name": "Empresa Flow",
    })
    r = client.post("/api/auth/login", json={"email": email, "password": "123456"})
    headers = {"Authorization": "Bearer " + r.json()["access_token"]}

    # Create
    r1 = client.post("/api/flows", headers=headers, json={
        "name": "Fluxo Manual",
        "description": "Teste",
        "nodes": [
            {"id": "a", "type": "message", "content": "Oi!", "next": "b"},
            {"id": "b", "type": "input", "content": "Nome?", "variable": "nome", "next": "c"},
            {"id": "c", "type": "end", "content": "Fim"},
        ],
    })
    assert r1.status_code == 201
    fid = r1.json()["id"]

    # Update
    r2 = client.put(f"/api/flows/{fid}", headers=headers, json={"name": "Fluxo Manual Atualizado"})
    assert r2.status_code == 200
    assert r2.json()["name"] == "Fluxo Manual Atualizado"

    # Delete
    r3 = client.delete(f"/api/flows/{fid}", headers=headers)
    assert r3.status_code == 204


def test_dashboard_metrics():
    email = f"dash_{os.urandom(3).hex()}@dialoga.com"
    client.post("/api/auth/register", json={
        "email": email,
        "password": "123456",
        "company_name": "Empresa Dash",
    })
    r = client.post("/api/auth/login", json={"email": email, "password": "123456"})
    headers = {"Authorization": "Bearer " + r.json()["access_token"}

    r = client.get("/api/dashboard/metrics", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "flows_count" in data
    assert "leads_count" in data
    assert "leads_by_day" in data


def test_unauthorized_access():
    """Rotas protegidas devem exigir token."""
    r = client.get("/api/auth/me")
    assert r.status_code == 401
    r = client.get("/api/flows")
    assert r.status_code == 401


def test_webhook_verify():
    """Webhook deve responder ao challenge do Meta."""
    r = client.get("/webhook/whatsapp", params={
        "hub.mode": "subscribe",
        "hub.verify_token": "dialoga-verify",
        "hub.challenge": "1234567890",
    })
    assert r.status_code == 200
    assert r.text == "1234567890"

    r2 = client.get("/webhook/whatsapp", params={
        "hub.mode": "subscribe",
        "hub.verify_token": "TOKEN-ERRADO",
        "hub.challenge": "1234567890",
    })
    assert r2.status_code == 403