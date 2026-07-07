# BACKUP PROMPT + NOVO ROADMAP — dIAloga+ 2.0

> Documento de continuidade para não perder o contexto do projeto caso este chat seja perdido.  
> Produto: **dIAloga+** — SaaS de automação de WhatsApp com IA, fluxos, CRM e atendimento humano.  
> Última atualização contextual: após validar conexão WhatsApp real via Evolution API/QR Code e antes de iniciar a Fase CRM global.

---

## 1. Prompt pronto para colar em uma nova IA

Copie e cole o texto abaixo em um novo chat caso precise continuar o projeto com outra IA.

```markdown
Você será meu assistente técnico principal para continuar o desenvolvimento do SaaS **dIAloga+ 2.0**.

Quero que você atue como **dev full-stack sênior + arquiteto de produto SaaS**, tomando decisões técnicas robustas, sem quebrar o que já funciona. Eu defino a visão de negócio; você decide a melhor engenharia.

Comunique-se sempre em **português do Brasil**, de forma didática, para nível iniciante-intermediário. Use tabelas e listas quando ajudar. Não faça “jeitinhos”: se algo estiver errado na arquitetura, proponha correção estrutural.

Princípios obrigatórios:

1. Toda feature nova deve ser **aditiva**, sem apagar tabelas nem quebrar produção.
2. Usar **feature flags** quando a feature tiver risco.
3. Sempre testar em sandbox antes de me entregar código.
4. Quando for me passar arquivos, prefira substituir o arquivo inteiro quando possível, porque edição manual de trechos já causou bugs.
5. Não assumir que `create_all()` altera tabelas existentes. O projeto não usa Alembic de verdade; usa `Base.metadata.create_all()`, então colunas novas em tabelas existentes precisam entrar em auto-migração aditiva no `database.py` ou, em último caso, SQL manual seguro no Neon.
6. Nunca pedir para eu usar comercialmente antes de todos os recursos principais estarem robustos.
7. Sempre preservar o que já está funcionando: login, fluxos, simulador, IA/RAG, WhatsApp Evolution conectado, etc.

---

# Contexto do produto

O projeto se chama **dIAloga+**. É um SaaS para empresas criarem chatbots/atendentes de WhatsApp com:

- fluxos guiados;
- IA com RAG;
- WhatsApp oficial Meta Cloud API;
- WhatsApp QR Code via Evolution API para testes/planos não-oficiais;
- CRM/Leads;
- handoff humano;
- dashboard;
- nichos verticais.

Estamos transformando o produto no **dIAloga+ 2.0**, verticalizado inicialmente em:

1. **Veículos**;
2. **Clínicas estética/odontologia**;
3. **Petshop**;
4. sem ser exclusivo: o produto pode atender outros segmentos também.

Modelo de negócio planejado:

- curso na Hotmart/Eduzz ensinando a vender automação;
- SaaS com recorrência/MRR;
- automação da própria venda do produto;
- planos sugeridos: Essencial R$147, Profissional R$297, Performance R$497;
- plano QR Code pode existir, mas com aviso de risco de banimento.

---

# Stack e infraestrutura

Backend:

- Python 3;
- FastAPI;
- SQLAlchemy 2.0;
- Pydantic;
- PostgreSQL Neon em produção;
- SQLite em dev/testes;
- Deploy no Render;
- Render usa Python 3.11.11;
- local do usuário usa Windows/PowerShell + venv Python 3.13.

Frontend:

- HTML/CSS/JS vanilla;
- sem framework;
- frontend static site no Render.

URLs de produção:

- Backend: `https://dialoga-backend-1slr.onrender.com`
- Frontend: `https://dialoga-frontend-8p28.onrender.com`
- GitHub: `labsmartsafe-png/dialoga-saas`

Pasta local do usuário:

```txt
C:\Users\Bem-vindo(a)\Desktop\whatsflow-saas\
```

Nome legado da pasta é `whatsflow-saas`, mas o produto é **dIAloga+**.

---

# Padrões importantes do código

Backend:

- models usam estilo clássico SQLAlchemy `Column(...)`, não `Mapped[]`;
- PKs são Integer autoincrement;
- helper `utcnow()` usado nos models;
- rotas usam padrão:
  - `Depends(get_db)`;
  - `Depends(get_current_user)`;
  - filtrar por `owner_id == current_user.id`;
  - saída com `Model.model_validate(...)`.

Frontend:

- usa `window.WFApi` em `frontend/js/api.js`;
- usa `window.WFAuth` em `frontend/js/auth.js`;
- token salvo no localStorage com chave **`whatsflow_token`**;
- não usar `dialoga-token`;
- dark mode usa `localStorage["dialoga-dark-mode"] === "1"`.

Banco:

- não confiar que `create_all()` adiciona colunas;
- existe auto-migração aditiva em `backend/app/database.py` via `_ADDITIVE_COLUMNS`;
- futuras colunas em tabelas existentes devem entrar ali;
- nunca dropar/alterar destrutivamente tabela de produção.

---

# Estado atual do projeto

## Já foi implementado/testado

### WhatsApp Meta Cloud API

- Modelos WhatsApp criados em `models_whatsapp.py`;
- webhook Meta em `/webhook/whatsapp/meta`;
- CRUD de conexões Meta;
- token criptografado com Fernet;
- envio teste Meta;
- problema conhecido: erro Meta `130497`, conta comercial restrita para enviar ao Brasil enquanto não verifica Business Manager.

Variáveis Meta/segurança:

```env
WHATSAPP_META_ENABLED=true/false
META_APP_SECRET=...
WA_FERNET_KEYS=...
```

### IA + RAG com Gemini

Implementado:

- `models_rag.py`;
- `services/ai_provider.py`;
- `services/rag_service.py`;
- `routers/ai.py`;
- tela `frontend/ia.html`.

Funcionalidades:

- bases de conhecimento;
- chunks;
- embeddings Gemini;
- busca por cosseno em Python, não pgvector, para funcionar em SQLite dev;
- IA responde com fallback anti-alucinação;
- limite mensal por cliente em `AISettings.monthly_ai_limit`;
- quando passa limite, transfere para humano.

Gemini:

- `GEMINI_API_KEY` configurada;
- `GEMINI_CHAT_MODEL=gemini-2.5-flash` corrigiu erro 429 de modelo antigo;
- embedding recomendado: `gemini-embedding-001` com 768 dimensões;
- free tier não pode uso comercial; ativar billing antes de vender.

### Builder/Fluxos

Funciona com nós:

```txt
+MSG
+PERG
+INPUT
+IA
+COND
+DELAY
+HUMANO
+FIM
```

Tipos internos:

```txt
message
question
input
ai
condition
delay
human
end
```

Correções importantes já feitas no motor de fluxo:

- não usar `or current_id` no `next`, pois isso causava loop;
- delay espera de verdade com `time.sleep`, limitado por `MAX_DELAY_SECONDS`;
- persistência de posição no canvas;
- `fromNodeId` corrigido;
- curvas suaves no canvas;
- modo de fluxo `guided` ou `ai_agent`;
- nó `ai` em fluxo guiado;
- modo `ai_agent` responde com RAG na entrada.

### Evolution API / WhatsApp QR Code

Evolution API foi colocada no Railway:

```txt
https://evolution-api-production-ad0b.up.railway.app
```

Versão observada:

```txt
2.3.7
```

Usuário possui a `AUTHENTICATION_API_KEY`, mas ela é secreta e não deve ser exposta.

Variáveis no Render backend:

```env
EVOLUTION_ENABLED=true
EVOLUTION_BASE_URL=https://evolution-api-production-ad0b.up.railway.app
EVOLUTION_GLOBAL_API_KEY=<chave secreta da Evolution>
PUBLIC_BASE_URL=https://dialoga-backend-1slr.onrender.com
```

Endpoints usados na Evolution:

- `POST /instance/create`;
- `GET /instance/connect/{instance}`;
- `GET /instance/connectionState/{instance}`;
- `POST /message/sendText/{instance}`;
- `DELETE /instance/logout/{instance}`;
- `DELETE /instance/delete/{instance}`.

Header:

```txt
apikey: <AUTHENTICATION_API_KEY>
```

Webhook Evolution no dIAloga+:

```txt
/webhook/whatsapp/evo
```

A autenticação do webhook usa:

```txt
Authorization: Bearer <segredo gerado>
```

Status mapeados:

```txt
open -> connected
connecting -> connecting
close -> disconnected
```

O QR Code conectou com sucesso em produção. Isso confirmou que:

- Evolution está rodando;
- dIAloga+ cria conexão;
- QR abre;
- WhatsApp conecta;
- webhook chama o backend.

### Problema de schema Neon resolvido manualmente

Ao tentar gerar QR, houve erro 500. Render Logs mostraram colunas ausentes na tabela `whatsapp_connections`, como:

```txt
access_token_last4 does not exist
```

Causa: tabela criada numa fase antiga e `create_all()` não adicionou colunas novas.

Foi recomendado executar SQL seguro no Neon:

```sql
ALTER TABLE whatsapp_connections
ADD COLUMN IF NOT EXISTS phone_number VARCHAR(40);

ALTER TABLE whatsapp_connections
ADD COLUMN IF NOT EXISTS flow_id INTEGER;

ALTER TABLE whatsapp_connections
ADD COLUMN IF NOT EXISTS phone_number_id VARCHAR(100);

ALTER TABLE whatsapp_connections
ADD COLUMN IF NOT EXISTS waba_id VARCHAR(100);

ALTER TABLE whatsapp_connections
ADD COLUMN IF NOT EXISTS access_token_enc TEXT;

ALTER TABLE whatsapp_connections
ADD COLUMN IF NOT EXISTS access_token_last4 VARCHAR(8);

ALTER TABLE whatsapp_connections
ADD COLUMN IF NOT EXISTS last_error TEXT;

ALTER TABLE whatsapp_connections
ADD COLUMN IF NOT EXISTS evolution_instance_name VARCHAR(150);

ALTER TABLE whatsapp_connections
ADD COLUMN IF NOT EXISTS evolution_api_key_enc TEXT;

ALTER TABLE whatsapp_connections
ADD COLUMN IF NOT EXISTS webhook_secret_enc TEXT;

ALTER TABLE whatsapp_connections
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP;

ALTER TABLE whatsapp_connections
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;

UPDATE whatsapp_connections
SET created_at = CURRENT_TIMESTAMP
WHERE created_at IS NULL;

UPDATE whatsapp_connections
SET updated_at = CURRENT_TIMESTAMP
WHERE updated_at IS NULL;
```

Depois disso, usuário conseguiu conectar QR.

---

# Estado funcional atual

WhatsApp via QR Code/Evolution está funcionando.

O usuário criou/testou um fluxo real de triagem para técnico de campo. O bot respondeu no WhatsApp real.

Fluxo de exemplo usado:

```txt
+MSG recepcao
  ↓
+PERG pergunta_suporte
  ├── Sim -> +INPUT pede_chamado -> +INPUT pede_local -> +INPUT pede_duvida -> +MSG aguarde_atendimento -> +HUMANO atendimento_humano
  └── Não -> +MSG envia_contatos_suporte -> +FIM fim_sem_chamado
```

Mensagens sugeridas:

`recepcao`:

```txt
Olá! Recebemos sua solicitação.

Antes de encaminhar seu atendimento, vamos fazer uma triagem rápida.
```

`pergunta_suporte`, tipo `+PERG`:

```txt
Você já fez contato com o setor de Suporte Operacional?
```

Opções:

| Label | Valor | Próximo |
|---|---|---|
| Sim, já fiz contato | sim | pede_chamado |
| Não, ainda não fiz contato | nao | envia_contatos_suporte |

`pede_chamado`, tipo `+INPUT`, variável `numero_chamado`:

```txt
Perfeito.

Informe, por favor, o número do chamado que você está atendendo.
```

`pede_local`, tipo `+INPUT`, variável `local_atendimento`:

```txt
Agora informe o local do atendimento.

Pode ser o endereço, nome da unidade, nome do cliente ou uma referência do local.
```

`pede_duvida`, tipo `+INPUT`, variável `duvida_tecnica`:

```txt
Descreva agora qual é a dúvida ou dificuldade encontrada no atendimento.
```

`aguarde_atendimento`, tipo `+MSG`:

```txt
Obrigado pelas informações.

Resumo do atendimento:

Chamado: {{numero_chamado}}
Local: {{local_atendimento}}
Dúvida informada: {{duvida_tecnica}}

Por favor, aguarde. Sua solicitação será encaminhada para atendimento humano.
```

`envia_contatos_suporte`, tipo `+MSG`:

```txt
Para seguir com o atendimento, é necessário primeiro fazer contato com o setor de Suporte Operacional.

Entre em contato por um dos canais abaixo:

WhatsApp/Telefone: (XX) XXXXX-XXXX
E-mail: suporte.operacional@suaempresa.com.br

Após abrir o chamado, envie uma nova mensagem por aqui informando o número do chamado, o local do atendimento e sua dúvida.
```

---

# Problema atual antes do próximo desenvolvimento

Depois de conectar WhatsApp e bot funcionar, o usuário percebeu:

```txt
Ao entrar em Leads, não atualizou.
```

Diagnóstico:

- o fluxo respondeu no WhatsApp;
- mas o CRM/Leads não foi alimentado corretamente;
- isso revelou que o projeto precisa de uma arquitetura global de Leads/CRM, não só um ajuste pontual no `flow_engine.py`.

Foi discutido que é melhor NÃO remendar apenas `_ensure_lead()` agora.

A próxima fase deve ser uma **Fase CRM global**, separando leads de:

```txt
simulator
whatsapp_evolution
whatsapp_meta
manual
import
api
```

E preparando:

- CRM;
- dashboard;
- inbox humano;
- ROI;
- funil por nicho;
- atendimento humano real;
- métricas sem poluir dados reais com testes do simulador.

---

# Decisão estratégica nova

Antes de implementar mais features como áudio, agenda ou dashboard ROI, vamos criar um **CRM/Leads global**.

Motivo:

Se não houver uma camada central de Leads, cada canal novo vai virar um remendo. O correto é padronizar agora:

```txt
mensagem recebida -> identifica contato -> cria/atualiza lead -> vincula conversa -> executa fluxo -> atualiza contexto/status/stage -> handoff/fim
```

---

# Novo Roadmap recomendado

## Fase CRM 1.0 — Base global de Leads e fontes

Objetivo: fazer Leads funcionar de forma profissional, separando simulador de canais reais.

Entregas:

1. Criar serviço central:

```txt
backend/app/services/lead_service.py
```

Responsabilidades:

- criar lead;
- atualizar lead;
- deduplicar por telefone/canal/fluxo;
- vincular lead à conversa;
- atualizar contexto;
- atualizar etapa `stage`;
- atualizar `status`;
- registrar origem;
- marcar handoff humano;
- marcar encerramento.

2. Padronizar fontes:

```txt
simulator
whatsapp_evolution
whatsapp_meta
manual
import
api
```

3. Ajustar `flow_engine.py` para usar `lead_service`, em vez de criar lead diretamente.

4. Ajustar `whatsapp_evolution.py` para passar contexto correto:

```txt
channel = whatsapp
provider = evolution
source = whatsapp_evolution
connection_id
wa_id
```

5. Ajustar Meta futura para usar:

```txt
source = whatsapp_meta
provider = meta
```

6. Atualizar tela Leads para mostrar claramente origem.

7. Criar filtros na tela Leads:

- todos;
- reais;
- simulador;
- WhatsApp QR;
- WhatsApp oficial;
- status;
- fluxo;
- data;
- busca por nome/telefone.

8. Dashboard não deve contar simulador como métrica real por padrão.

9. Simulador pode gerar leads de teste, mas com `source=simulator` e filtro separado.

Campos mínimos recomendados no Lead:

Atualmente o `Lead` já tem:

```txt
owner_id
flow_id
name
phone
email
stage
context
source
status
created_at
```

Adicionar de forma aditiva, se ainda não existir:

```txt
conversation_id
connection_id
last_interaction_at
last_message_at
assigned_to
```

Ou começar mais simples com:

```txt
conversation_id
connection_id
last_interaction_at
```

Sempre via auto-migração aditiva em `database.py`.

Status recomendados:

```txt
novo
em_atendimento
aguardando_humano
qualificado
agendado
convertido
perdido
encerrado
```

Stages recomendados iniciais:

```txt
inicio
pergunta_suporte
pede_chamado
pede_local
pede_duvida
aguardando_humano
fim
```

Regras por nó:

| Nó | Efeito no Lead |
|---|---|
| +MSG | pode atualizar stage |
| +PERG | salva escolha se houver variável/opção |
| +INPUT | salva variável no contexto e atualiza lead |
| +IA | registra atendimento por IA |
| +COND | registra caminho escolhido, se possível |
| +DELAY | geralmente não altera |
| +HUMANO | status `aguardando_humano` |
| +FIM | status `encerrado` |

---

## Fase CRM 1.1 — Inbox humano

Objetivo: transformar o `+HUMANO` em uma fila operacional real.

Entregas:

- tela de conversas/inbox;
- filtro `aguardando humano`;
- histórico de mensagens;
- botão “assumir atendimento”;
- botão “encerrar atendimento”;
- notas internas;
- status operacional;
- responsável pelo atendimento;
- separação bot ativo vs humano assumiu.

---

## Fase CRM 1.2 — Pipeline/funil por nicho

Objetivo: verticalizar o CRM.

Funil veículos:

```txt
Novo lead
Qualificado
Agendou visita
Visitou loja
Proposta enviada
Vendido
Perdido
```

Funil clínicas:

```txt
Novo lead
Qualificado
Agendamento pendente
Consulta marcada
Compareceu
Fechou procedimento
Perdido
```

Funil petshop:

```txt
Novo cliente
Agendamento pendente
Agendado
Atendido
Retorno/lembrete
Reativação
```

Funil suporte técnico:

```txt
Novo contato
Chamado confirmado
Dados coletados
Aguardando humano
Em atendimento
Resolvido
Encerrado
```

---

## Fase CRM 1.3 — Timeline/Eventos

Criar eventos do lead:

```txt
lead_events
```

Campos sugeridos:

```txt
id
owner_id
lead_id
conversation_id
event_type
title
payload
created_at
```

Eventos:

```txt
lead_created
message_received
message_sent
flow_started
input_collected
question_answered
handoff_requested
conversation_closed
status_changed
note_added
tag_added
```

---

## Fase CRM 1.4 — Tags, notas e tarefas

Recursos:

- tags manuais;
- tags automáticas por fluxo;
- notas internas;
- tarefas/lembretes;
- “retornar em X minutos”;
- prioridade;
- urgência.

---

## Fase B — Áudio no WhatsApp

Depois da base CRM, implementar áudio.

Objetivo:

- receber áudio no WhatsApp;
- transcrever com Gemini multimodal;
- alimentar fluxo/IA como texto;
- futuramente responder com áudio.

Por que depois do CRM?

Porque áudio também precisa registrar contexto, lead, timeline e última interação.

---

## Fase C — Agendamento + ROI

Para clínicas, petshop e veículos.

Entregas:

- modelo `Appointment`;
- Google Calendar OAuth;
- disponibilidade;
- confirmação;
- lembrete;
- no-show;
- dashboard de receita recuperada.

---

## Fase D — Dashboard de performance e ROI

Métricas:

- leads reais;
- leads por origem;
- leads por fluxo;
- taxa de resposta;
- tempo médio até primeira resposta;
- handoffs humanos;
- conversas encerradas;
- agendamentos;
- receita estimada;
- ROI por campanha/nicho.

Importante: simulador não entra nas métricas reais por padrão.

---

## Fase E — Gerador de fluxo por IA + setup guiado

Objetivo:

- usuário escolhe nicho;
- responde perguntas;
- IA cria fluxo inicial;
- IA sugere mensagens;
- IA sugere base de conhecimento;
- setup guiado em poucos passos.

---

## Fase F — Pacotes por nicho

Templates prontos:

- veículos;
- clínicas estética/odonto;
- petshop;
- suporte técnico;
- serviços locais.

Cada pacote deve ter:

- fluxo;
- base de conhecimento modelo;
- funil;
- tags;
- mensagens;
- dashboard sugerido.

---

## Fase G — Robustez, fila, billing e go-live

Antes de vender:

- Render backend em plano pago;
- Business Verification Meta;
- billing Gemini ativado;
- decidir custo de IA;
- fila assíncrona com Redis/arq;
- idempotência robusta;
- logs melhores;
- painel admin;
- planos e limites;
- integração Hotmart/Eduzz para liberar acesso.

---

# Pendências importantes

## Painel Admin

Ainda não existe `is_admin`/`role` no User nem painel admin.

Fazer depois das features principais.

Escopo:

- listar usuários;
- ativar/desativar usuário;
- alterar plano;
- métricas gerais;
- leads por cliente;
- consumo IA por cliente;
- gráficos;
- liberar acesso por pagamento Hotmart/Eduzz futuramente.

## Decisão de custo de IA

Lembrar no final do projeto:

- usar `gemini-2.5-flash-lite`?
- permitir BYOK: cliente traz chave própria?
- créditos/recarga?
- ativar billing Gemini?
- free tier não pode uso comercial.

## Go-live

Antes de vender:

- subir Render backend para plano pago;
- Business Verification Meta;
- billing Gemini;
- política de privacidade;
- termos;
- aviso de risco para plano QR Code;
- monitoramento/logs.

---

# Arquivos relevantes

Backend:

```txt
backend/app/main.py
backend/app/config.py
backend/app/database.py
backend/app/models.py
backend/app/models_whatsapp.py
backend/app/models_rag.py
backend/app/crypto.py
backend/app/schemas.py
backend/app/schemas_whatsapp.py
backend/app/schemas_rag.py
backend/app/auth.py
backend/app/json.py
backend/app/routers/auth.py
backend/app/routers/templates.py
backend/app/routers/flows.py
backend/app/routers/leads.py
backend/app/routers/dashboard.py
backend/app/routers/whatsapp.py
backend/app/routers/whatsapp_meta.py
backend/app/routers/whatsapp_connections.py
backend/app/routers/whatsapp_evolution.py
backend/app/routers/ai.py
backend/app/services/flow_engine.py
backend/app/services/template_loader.py
backend/app/services/whatsapp_service.py
backend/app/services/whatsapp_meta_service.py
backend/app/services/ai_provider.py
backend/app/services/rag_service.py
backend/app/services/evolution_service.py
```

Frontend:

```txt
frontend/index.html
frontend/login.html
frontend/dashboard.html
frontend/builder.html
frontend/simulator.html
frontend/leads.html
frontend/configuracoes.html
frontend/ia.html
frontend/js/api.js
frontend/js/auth.js
frontend/js/canvas.js
frontend/js/builder.js
frontend/js/simulator.js
frontend/js/dashboard.js
```

Docs existentes/importantes:

```txt
docs/GUIA_WHATSAPP_PLANOS.md
docs/GUIA_CRIAR_APP_META.md
docs/ROADMAP_dIAloga_2.0.md
docs/PITCH_E_NEGOCIO_dIAloga_2.0.md
```

---

# O que a nova IA deve pedir ao usuário antes de alterar código

Para continuar de forma segura, peça que o usuário envie ou confirme:

1. Arquivos atuais do backend:

```txt
backend/app/models.py
backend/app/database.py
backend/app/schemas.py
backend/app/routers/leads.py
backend/app/routers/flows.py
backend/app/routers/whatsapp_evolution.py
backend/app/services/flow_engine.py
```

2. Arquivos atuais do frontend:

```txt
frontend/leads.html
frontend/js/api.js
frontend/configuracoes.html
frontend/js/builder.js
frontend/js/canvas.js
```

3. Confirmar se o último deploy está live no Render.

4. Confirmar se o WhatsApp QR ainda conecta e responde.

5. Confirmar quais colunas existem em `leads`, `conversations` e `whatsapp_connections` no Neon, se houver erro 500.

6. Antes de qualquer alteração, rodar testes de sintaxe:

```bash
python -m py_compile backend/app/services/flow_engine.py
python -m py_compile backend/app/routers/whatsapp_evolution.py
python -m py_compile backend/app/database.py
node --check frontend/js/api.js
node --check frontend/js/builder.js
node --check frontend/js/canvas.js
```

7. Se criar colunas novas, testar auto-migração em SQLite antigo no sandbox antes de entregar.

---

# Observação sobre um patch testado mas não necessariamente aplicado

Foi preparado/testado no sandbox um patch em `flow_engine.py` para criar lead no início da conversa WhatsApp e atualizar contexto a cada `+INPUT`. Teste do sandbox:

```txt
OK: lead WhatsApp criado no inicio e atualizado com INPUT
```

Mas o usuário decidiu pausar antes de aplicar, para desenhar uma solução global de CRM. Portanto, a nova IA não deve simplesmente aplicar esse patch isolado sem antes implementar a estratégia global com `lead_service.py`.

---

# Recomendação imediata para a nova IA

O próximo desenvolvimento recomendado é:

```txt
Fase CRM 1.0 — Base global de Leads e fontes
```

Não começar por áudio, agenda ou dashboard antes de resolver Leads globalmente.

A primeira entrega técnica ideal:

1. Criar `backend/app/services/lead_service.py`;
2. Adicionar colunas aditivas mínimas em `Lead` se necessário;
3. Atualizar `database.py` com auto-migração;
4. Refatorar `flow_engine.py` para usar `lead_service`;
5. Ajustar `whatsapp_evolution.py` para passar origem/conexão corretamente;
6. Ajustar `routers/leads.py` e schemas para expor origem/status/stage/context/última interação;
7. Ajustar `frontend/leads.html` para diferenciar Simulador vs WhatsApp QR;
8. Testar em SQLite e, depois, produção.
```

---

## 2. Roadmap executivo resumido

| Fase | Nome | Objetivo | Prioridade |
|---|---|---|---|
| CRM 1.0 | Leads globais e fontes | Separar simulador/WhatsApp e criar lead real corretamente | Altíssima |
| CRM 1.1 | Inbox humano | Fazer `+HUMANO` virar fila operacional | Alta |
| CRM 1.2 | Funil por nicho | Pipelines para veículos, clínicas, petshop e suporte | Alta |
| CRM 1.3 | Timeline/eventos | Histórico completo do lead | Média/Alta |
| CRM 1.4 | Tags, notas e tarefas | CRM mais avançado | Média |
| B | Áudio | Transcrição e uso de áudio no WhatsApp | Alta após CRM |
| C | Agendamento | Google Calendar, lembretes e no-show | Alta |
| D | Dashboard ROI | Métricas reais, sem misturar simulador | Alta |
| E | Gerador IA | Setup guiado e criação de fluxos por IA | Média/Alta |
| F | Nichos prontos | Empacotar verticais | Alta comercial |
| G | Robustez/billing | Go-live, plano pago, admin, billing e filas | Obrigatória antes de vender |

---

## 3. Decisão de arquitetura atual

A decisão mais importante tomada agora:

> Antes de continuar com novas features, o dIAloga+ precisa de uma base global de CRM/Leads.

Motivo:

- WhatsApp real já funciona;
- fluxo real já responde;
- mas lead não atualizou;
- isso revela que a camada de negócio precisa amadurecer;
- CRM é o centro do produto, principalmente para vender ROI.

---

## 4. Critérios de sucesso da Fase CRM 1.0

A fase só deve ser considerada pronta quando:

1. Lead do simulador aparece como `simulator` ou fica filtrado como teste;
2. Lead de WhatsApp QR aparece como `whatsapp_evolution`;
3. Lead de Meta oficial, quando usado, aparece como `whatsapp_meta`;
4. Conversa fica vinculada ao lead;
5. `+INPUT` atualiza `context` do lead;
6. `+PERG` salva escolha quando houver variável/opção relevante;
7. `+HUMANO` muda status para `aguardando_humano`;
8. `+FIM` muda status para `encerrado`;
9. Tela Leads permite filtrar por origem;
10. Dashboard não conta simulador como produção por padrão;
11. Tudo funciona sem quebrar WhatsApp QR já conectado.

---

## 5. Notas finais

Este projeto já avançou bastante. Os marcos mais importantes alcançados:

- IA/RAG funcionando;
- builder com nós avançados;
- modo IA agente;
- Meta Cloud API parcialmente integrada;
- Evolution API QR Code funcionando em produção;
- WhatsApp real conectado;
- fluxo real respondendo;
- schema antigo do Neon corrigido manualmente;
- decisão de evoluir o CRM antes de novas features.

A próxima IA deve tratar esse documento como fonte de continuidade e pedir os arquivos atuais antes de qualquer patch grande.
