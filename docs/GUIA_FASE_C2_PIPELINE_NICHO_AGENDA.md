# Guia — Fase C.2: Pipeline por nicho + Agenda avançada

## Objetivo

Integrar pipeline comercial por nicho com a agenda interna, já deixando campos preparados para futura integração com Google Calendar.

## O que foi implementado

### Lead

Novos campos em `leads`:

```txt
pipeline_type VARCHAR(50) DEFAULT 'generic'
pipeline_stage VARCHAR(100) DEFAULT 'novo'
```

### Appointment

Novos campos em `appointments`:

```txt
appointment_type VARCHAR(50) DEFAULT 'generic'
external_calendar_provider VARCHAR(50)
external_event_id VARCHAR(255)
calendar_sync_status VARCHAR(50) DEFAULT 'not_synced'
calendar_last_error TEXT
```

Os campos `external_*` e `calendar_*` ainda não sincronizam com Google. Eles deixam a base preparada para a Fase C.2.3.

## Tipos de agendamento

```txt
generic
avaliacao
consulta
banho_tosa
visita
test_drive
retorno
suporte
```

## Pipelines automáticos

### Genérico

```txt
solicitado -> agendamento_pendente
confirmado -> agendado
realizado -> realizado
nao_compareceu -> no_show
cancelado -> cancelado
```

### Clínica

Usado para `avaliacao` e `consulta`:

```txt
solicitado -> agendamento_pendente
confirmado -> avaliacao_marcada
realizado -> compareceu
nao_compareceu -> no_show
cancelado -> cancelado
```

### Petshop

Usado para `banho_tosa`:

```txt
solicitado -> agendamento_pendente
confirmado -> banho_tosa_marcado
realizado -> atendido
nao_compareceu -> no_show
cancelado -> cancelado
```

### Veículos

Usado para `visita` e `test_drive`:

```txt
solicitado -> agendamento_pendente
confirmado -> visita_marcada
realizado -> compareceu
nao_compareceu -> no_show
cancelado -> cancelado
```

### Suporte técnico

Usado para `suporte`:

```txt
solicitado -> agendamento_pendente
confirmado -> agendado
realizado -> resolvido
nao_compareceu -> no_show
cancelado -> cancelado
```

## Regras automáticas

Quando um agendamento é criado ou atualizado:

1. identifica o tipo de agendamento;
2. define `lead.pipeline_type` se necessário;
3. atualiza `lead.pipeline_stage` conforme o status do agendamento.

Exemplo:

```txt
appointment_type = avaliacao
status = confirmado
```

Resultado:

```txt
lead.pipeline_type = clinica
lead.pipeline_stage = avaliacao_marcada
```

## Frontend

### Agenda

Em `frontend/agenda.html`, foi adicionado campo:

```txt
Tipo de agendamento
```

Opções:

```txt
Genérico
Avaliação clínica
Consulta
Banho e tosa
Visita
Test-drive
Retorno
Suporte técnico
```

### Leads

Em `frontend/leads.html`, o lead exibe:

```txt
pipeline_type / pipeline_stage
```

### Dashboard

Em `frontend/dashboard.html`, foi adicionada tabela:

```txt
Pipeline por nicho/etapa
```

## Backend alterado

```txt
backend/app/models.py
backend/app/database.py
backend/app/schemas.py
backend/app/routers/appointments.py
backend/app/routers/leads.py
backend/app/routers/dashboard.py
```

## Frontend alterado

```txt
frontend/agenda.html
frontend/leads.html
frontend/dashboard.html
```

## Testes feitos no sandbox

```txt
python -m py_compile backend/app/models.py backend/app/database.py backend/app/schemas.py backend/app/routers/appointments.py backend/app/routers/leads.py backend/app/routers/dashboard.py
node --check frontend/js/api.js
node --check /tmp/agenda_inline.js
node --check /tmp/leads_inline.js
node --check /tmp/dashboard_inline.js
OK: pipeline por nicho + agenda avançada funcionando
```

## Como aplicar

Substitua os arquivos:

```txt
backend/app/models.py
backend/app/database.py
backend/app/schemas.py
backend/app/routers/appointments.py
backend/app/routers/leads.py
backend/app/routers/dashboard.py
frontend/agenda.html
frontend/leads.html
frontend/dashboard.html
docs/GUIA_FASE_C2_PIPELINE_NICHO_AGENDA.md
```

Valide:

```powershell
python -m py_compile backend/app/models.py backend/app/database.py backend/app/schemas.py backend/app/routers/appointments.py backend/app/routers/leads.py backend/app/routers/dashboard.py
node --check frontend/js/api.js
```

Commit:

```powershell
git add backend/app/models.py backend/app/database.py backend/app/schemas.py backend/app/routers/appointments.py backend/app/routers/leads.py backend/app/routers/dashboard.py frontend/agenda.html frontend/leads.html frontend/dashboard.html docs/GUIA_FASE_C2_PIPELINE_NICHO_AGENDA.md
git commit -m "Adiciona pipeline por nicho integrado a agenda"
git push
```

## Teste em produção

1. Abrir `/agenda.html`.
2. Criar um agendamento com tipo `Avaliação clínica`.
3. Marcar status como `Confirmado`.
4. Abrir o lead em `/leads.html`.
5. Verificar:

```txt
clinica / avaliacao_marcada
```

6. Alterar agendamento para `Realizado`.
7. Verificar que o lead muda para:

```txt
clinica / compareceu
```

8. Abrir `/dashboard.html` e conferir a tabela `Pipeline por nicho/etapa`.

## Próximo passo recomendado

Fase C.2.3 — Google Calendar OAuth e sincronização real dos eventos.
