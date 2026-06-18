# 📘 WhatsFlow SaaS — Documentação Principal

> Plataforma para criação de chatbots de WhatsApp com templates prontos para diversos nichos.

---

## ✨ Visão geral

O **WhatsFlow** permite que empresas criem chatbots de WhatsApp em minutos, sem programar. O usuário:

1. Cria uma conta gratuita.
2. Escolhe um **template** pronto (veículos, clínicas, imobiliárias etc.).
3. **Edita os nós** do fluxo (mensagens, perguntas, inputs, condições).
4. **Testa no simulador** integrado ao navegador.
5. Exporta os **leads** capturados para CSV.

A integração real com o WhatsApp Cloud API (Meta) está preparada — basta configurar as variáveis de ambiente.

---

## 📂 Estrutura do projeto

```
whatsflow-saas/
├── backend/                  # API Python + FastAPI
│   ├── app/
│   │   ├── main.py           # Entrypoint FastAPI
│   │   ├── config.py         # Configurações
│   │   ├── database.py       # SQLAlchemy
│   │   ├── models.py         # User, Flow, Lead, Template, Conversation, Message
│   │   ├── schemas.py        # Pydantic
│   │   ├── auth.py           # JWT + bcrypt
│   │   ├── routers/          # auth, templates, flows, leads, whatsapp, dashboard
│   │   ├── services/         # flow_engine, template_loader, whatsapp_service
│   │   └── templates_data/   # (espelho de /templates)
│   ├── alembic/              # Migrações
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── render.yaml
│   └── .env.example
├── frontend/                 # HTML5 + CSS3 + JS vanilla
│   ├── index.html            # Landing page
│   ├── login.html            # Login / Registro
│   ├── dashboard.html        # Painel
│   ├── builder.html          # Editor de fluxos + simulador (modal)
│   ├── simulator.html        # Simulador standalone
│   ├── leads.html            # Gestão de leads
│   ├── css/styles.css
│   └── js/
│       ├── api.js            # Cliente HTTP
│       ├── auth.js           # Helpers de auth
│       ├── dashboard.js
│       ├── builder.js
│       └── simulator.js
├── templates/                # Templates JSON (8 nichos)
│   ├── veiculos.json
│   ├── clinica.json
│   ├── imobiliaria.json
│   ├── restaurante.json
│   ├── academias.json
│   ├── salao-beleza.json
│   ├── petshop.json
│   └── e-commerce.json
├── data/                     # Banco SQLite + uploads
├── docs/                     # README, plano de negócio
├── tests/                    # Testes pytest
├── docker-compose.yml
└── .gitignore
```

---

## 🚀 Como executar localmente

### 1. Pré-requisitos

- **Python 3.11+**
- **pip** (gerenciador de pacotes)
- Opcional: **Docker** + **Docker Compose**

### 2. Instalação

```bash
# Clone o repositório
cd whatsflow-saas

# Crie e ative um ambiente virtual
python -m venv venv
source venv/bin/activate     # Linux/Mac
# venv\Scripts\activate      # Windows

# Instale as dependências
cd backend
pip install -r requirements.txt

# Copie o .env.example para .env
cp .env.example .env
```

### 3. Inicie o backend

```bash
# A partir de /backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Acesse:
- **API**: http://localhost:8000
- **Docs interativas (Swagger)**: http://localhost:8000/docs
- **Health check**: http://localhost:8000/health

### 4. Sirva o frontend

Você pode usar qualquer servidor estático. Exemplo com Python:

```bash
# A partir da raiz whatsflow-saas/
cd frontend
python -m http.server 5500
```

Acesse:
- **Landing**: http://localhost:5500
- **Login**: http://localhost:5500/login.html
- **Dashboard**: http://localhost:5500/dashboard.html

> 💡 **Alternativa simples:** abra `frontend/index.html` direto no navegador, mas o login precisará do backend rodando.

### 5. (Alternativa) Docker Compose

```bash
# A partir da raiz whatsflow-saas/
docker compose up --build
```

Isso sobe o backend + PostgreSQL.

### 6. Rodar os testes

```bash
cd whatsflow-saas
pip install pytest httpx
pytest tests/ -v
```

---

## 🔐 Variáveis de ambiente

Copie `backend/.env.example` para `backend/.env` e ajuste:

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `APP_ENV` | development | Ambiente |
| `DEBUG` | True | Modo debug |
| `SECRET_KEY` | (gerar) | Chave JWT (mínimo 64 caracteres em produção) |
| `JWT_EXPIRATION_MINUTES` | 43200 | Validade do token (30 dias) |
| `DATABASE_URL` | sqlite:///./data/whatsflow.db | URL do banco |
| `CORS_ORIGINS` | http://localhost:3000,... | Origens CORS permitidas |
| `WHATSAPP_TOKEN` | (vazio) | Token Meta (opcional no MVP) |
| `WHATSAPP_PHONE_ID` | (vazio) | ID do número |
| `WHATSAPP_VERIFY_TOKEN` | whatsflow-verify | Token de verificação do webhook |

Para gerar uma SECRET_KEY segura:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

---

## 🧩 Endpoints principais da API

Todos os endpoints (exceto `/health`, `/`, `/webhook/*`, `/api/auth/*`) exigem **Authorization: Bearer <token>**.

### Auth
- `POST /api/auth/register` — Cadastro
- `POST /api/auth/login` — Login
- `GET /api/auth/me` — Perfil
- `POST /api/auth/password-reset/request` — Solicitar reset
- `POST /api/auth/password-reset/confirm` — Confirmar nova senha

### Templates
- `GET /api/templates` — Lista todos
- `GET /api/templates/{slug}` — Detalhe
- `POST /api/templates/{slug}/import` — Importa como fluxo

### Fluxos
- `GET /api/flows` — Lista do usuário
- `POST /api/flows` — Criar
- `GET /api/flows/{id}` — Detalhe
- `PUT /api/flows/{id}` — Atualizar
- `DELETE /api/flows/{id}` — Excluir
- `POST /api/flows/{id}/simulate/start` — Iniciar simulação
- `POST /api/flows/simulate/message` — Enviar resposta

### Leads
- `GET /api/leads` — Listar (com filtros)
- `PUT /api/leads/{id}` — Atualizar
- `DELETE /api/leads/{id}` — Excluir
- `GET /api/leads/export/csv` — Exportar CSV

### Dashboard
- `GET /api/dashboard/metrics` — Métricas agregadas

### WhatsApp
- `GET /webhook/whatsapp` — Verificação Meta
- `POST /webhook/whatsapp` — Recebimento de mensagens
- `POST /api/whatsapp/send` — Enviar mensagem

---

## 🛠️ Motor de Fluxo

Tipos de nós suportados:

| Tipo      | Descrição |
|-----------|-----------|
| `message` | Envia uma mensagem automática |
| `question` | Mostra opções que o usuário pode escolher |
| `input` | Aguarda texto livre |
| `condition` | Desvia com base em variável do contexto |
| `delay`   | Espera N segundos (ignorada no simulador) |
| `webhook` | Aciona chamada HTTP externa |
| `human`   | Encaminha para atendimento humano |
| `end`     | Finaliza a conversa e captura lead |

### Contexto

Variáveis são capturadas durante a conversa (`{{nome}}`, `{{telefone}}`, etc.) e usadas para:
- **Substituição em mensagens** (renderização de `{{variavel}}`).
- **Salvamento automático** do lead ao final.

---

## 🚀 Deploy no Render

### Passo a passo

1. Suba o projeto para um repositório Git (GitHub, GitLab, etc.).
2. No Render, clique em **New → Blueprint**.
3. Aponte para o repositório.
4. Render detectará `backend/render.yaml` e criará:
   - Web service `whatsflow-backend` (FastAPI)
   - Static site `whatsflow-frontend`
   - PostgreSQL database `whatsflow-db`
5. As variáveis de ambiente serão geradas automaticamente. Personalize se necessário.
6. Aguarde o deploy. Acesse a URL gerada.

> ⚠️ Configure a variável `CORS_ORIGINS` com a URL do frontend no Render (ex: `https://whatsflow-frontend.onrender.com`).

### Configuração manual (alternativa)

Se preferir configurar sem `render.yaml`:
- **Backend**: New → Web Service → Runtime: Python → Build: `pip install -r requirements.txt` → Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Frontend**: New → Static Site → Publish Path: `frontend`
- **Banco**: New → PostgreSQL

---

## 🤖 Integração WhatsApp Cloud API

### Webhook
1. No Meta for Developers, configure o webhook apontando para `https://<seu-dominio>/webhook/whatsapp`.
2. Use o valor de `WHATSAPP_VERIFY_TOKEN` como **Verify Token**.
3. O endpoint responde corretamente ao desafio do Meta (challenge).

### Envio de mensagens
Para enviar mensagens reais, configure no `.env`:
```
WHATSAPP_TOKEN=<seu-token-meta>
WHATSAPP_PHONE_ID=<id-do-numero>
WHATSAPP_API_URL=https://graph.facebook.com/v18.0
```

Depois, use o endpoint autenticado:
```bash
curl -X POST https://api.whatsflow.com/api/whatsapp/send \
  -H "Authorization: Bearer <seu-jwt>" \
  -H "Content-Type: application/json" \
  -d '{"to": "5511999999999", "text": "Olá!"}'
```

---

## 🧪 Testes

```bash
pytest tests/ -v
```

Os testes cobrem:
- ✅ Health check
- ✅ Registro e login
- ✅ Validação de erros (e-mail duplicado, senha errada)
- ✅ Listagem e importação de templates
- ✅ CRUD de fluxos
- ✅ Simulação completa
- ✅ Dashboard
- ✅ Acesso não autorizado
- ✅ Webhook do WhatsApp

---

## 📝 Licença

MIT — use livremente, modifique, distribua.

---

## 📞 Contato

- **E-mail**: contato@whatsflow.com.br
- **Documentação adicional**: veja [PLANO-DE-NEGOCIO.md](PLANO-DE-NEGOCIO.md) e [RESUMO-EXECUTIVO.md](RESUMO-EXECUTIVO.md)
