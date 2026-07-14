# Guia — Fase C.1: Agenda interna

## Objetivo

Criar a primeira versão de agendamentos do dIAloga+, ainda sem Google Calendar.

Essa fase permite registrar compromissos vinculados a leads, como:

- avaliação clínica;
- consulta odontológica;
- banho e tosa;
- visita à loja;
- test-drive;
- ligação de retorno;
- atendimento técnico.

## Arquivos criados

```txt
backend/app/routers/appointments.py
frontend/agenda.html
docs/GUIA_FASE_C1_AGENDA_INTERNA.md
```

## Arquivos alterados

```txt
backend/app/models.py
backend/app/schemas.py
backend/app/main.py
frontend/js/api.js
frontend/dashboard.html
frontend/builder.html
frontend/leads.html
frontend/inbox.html
frontend/ia.html
frontend/configuracoes.html
```

## Novo model

Tabela:

```txt
appointments
```

Campos:

```txt
id
owner_id
lead_id
flow_id
title
scheduled_at
status
notes
created_at
updated_at
```

Status disponíveis:

```txt
solicitado
confirmado
cancelado
realizado
nao_compareceu
```

Como é tabela nova, `Base.metadata.create_all()` cria automaticamente. Não precisa adicionar em `_ADDITIVE_COLUMNS`.

## Novos schemas

```txt
AppointmentCreate
AppointmentUpdate
AppointmentOut
```

## Novo router

```txt
backend/app/routers/appointments.py
```

Prefixo:

```txt
/api/appointments
```

Endpoints:

```txt
GET /api/appointments
POST /api/appointments
GET /api/appointments/{id}
PUT /api/appointments/{id}
DELETE /api/appointments/{id}
```

Filtros disponíveis no GET:

```txt
status
lead_id
flow_id
date_from
date_to
```

## Frontend

Nova tela:

```txt
frontend/agenda.html
```

Funcionalidades:

- criar agendamento;
- editar agendamento;
- excluir agendamento;
- alterar status rapidamente;
- filtrar por status;
- filtrar por data;
- vincular lead;
- exibir telefone/nome do lead;
- dark mode básico.

## API JS

Adicionados em `frontend/js/api.js`:

```js
listAppointments(qs)
createAppointment(body)
updateAppointment(id, body)
deleteAppointment(id)
```

## Menu

A guia `Agenda` foi adicionada nos menus principais:

```txt
Dashboard
Fluxos
Leads
Inbox
Agenda
IA
Configurações
```

## Testes feitos no sandbox

```txt
python -m py_compile backend/app/models.py backend/app/schemas.py backend/app/routers/appointments.py backend/app/main.py
node --check frontend/js/api.js
node --check /tmp/agenda_inline.js
OK html clean/menu agenda
OK: CRUD agenda interna funcionando
```

## Como aplicar

Substitua/crie os arquivos:

```txt
backend/app/models.py
backend/app/schemas.py
backend/app/main.py
backend/app/routers/appointments.py
frontend/js/api.js
frontend/agenda.html
frontend/dashboard.html
frontend/builder.html
frontend/leads.html
frontend/inbox.html
frontend/ia.html
frontend/configuracoes.html
docs/GUIA_FASE_C1_AGENDA_INTERNA.md
```

Valide:

```powershell
python -m py_compile backend/app/models.py backend/app/schemas.py backend/app/routers/appointments.py backend/app/main.py
node --check frontend/js/api.js
```

Commit:

```powershell
git add backend/app/models.py backend/app/schemas.py backend/app/main.py backend/app/routers/appointments.py frontend/js/api.js frontend/agenda.html frontend/dashboard.html frontend/builder.html frontend/leads.html frontend/inbox.html frontend/ia.html frontend/configuracoes.html docs/GUIA_FASE_C1_AGENDA_INTERNA.md
git commit -m "Adiciona agenda interna"
git push
```

## Teste em produção

1. Aguardar deploy backend/frontend.
2. Abrir:

```txt
/agenda.html
```

3. Criar um agendamento vinculado a um lead.
4. Alterar status para `confirmado`.
5. Filtrar por data/status.
6. Excluir o agendamento de teste.

## Próximo passo recomendado

Depois de validar:

1. Adicionar botão `Criar agendamento` dentro da Inbox para pré-selecionar o lead;
2. Mostrar próximos agendamentos no Dashboard;
3. Fase C.2 — Google Calendar OAuth.
