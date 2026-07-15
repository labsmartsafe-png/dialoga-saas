# Guia — Fase C.2.3: Google Calendar OAuth + Sync

## Objetivo

Conectar o dIAloga+ ao Google Calendar e sincronizar agendamentos internos como eventos no calendário.

## Arquivos criados

```txt
backend/app/services/google_calendar_service.py
backend/app/routers/calendar.py
docs/GUIA_FASE_C2_3_GOOGLE_CALENDAR.md
```

## Arquivos alterados

```txt
backend/app/config.py
backend/app/models.py
backend/app/main.py
backend/app/routers/appointments.py
frontend/js/api.js
frontend/configuracoes.html
frontend/agenda.html
```

## Novas variáveis de ambiente no Render backend

```env
GOOGLE_CALENDAR_ENABLED=true
GOOGLE_CLIENT_ID=<client id do Google Cloud>
GOOGLE_CLIENT_SECRET=<client secret do Google Cloud>
GOOGLE_REDIRECT_URI=https://dialoga-backend-1slr.onrender.com/api/calendar/google/callback
FRONTEND_BASE_URL=https://dialoga-frontend-8p28.onrender.com
```

Observação: `GOOGLE_REDIRECT_URI` pode ficar vazio porque o backend monta com `PUBLIC_BASE_URL`, mas é melhor configurar explicitamente no Render.

## Google Cloud Console

Criar OAuth Client:

Tipo:

```txt
Web application
```

Authorized redirect URI:

```txt
https://dialoga-backend-1slr.onrender.com/api/calendar/google/callback
```

Escopo usado:

```txt
https://www.googleapis.com/auth/calendar.events
```

## Novo model

```txt
CalendarConnection
```

Tabela:

```txt
calendar_connections
```

Campos:

```txt
owner_id
provider
status
calendar_id
access_token_enc
refresh_token_enc
token_expires_at
last_error
created_at
updated_at
```

Tokens são criptografados com `WA_FERNET_KEYS`.

## Endpoints novos

Prefixo:

```txt
/api/calendar
```

### Gerar URL OAuth

```txt
GET /api/calendar/google/auth-url
```

### Callback OAuth público

```txt
GET /api/calendar/google/callback
```

### Ver status

```txt
GET /api/calendar/status
```

### Desconectar

```txt
POST /api/calendar/disconnect
```

### Sincronizar agendamento manualmente

```txt
POST /api/calendar/sync-appointment/{appointment_id}
```

## Frontend

### Configurações

Em:

```txt
frontend/configuracoes.html
```

Foi adicionado card:

```txt
Google Calendar
```

Botões:

```txt
Conectar Google Calendar
Desconectar calendário
```

### Agenda

Em:

```txt
frontend/agenda.html
```

Foi adicionado:

```txt
Sync Google
```

E exibição de status:

```txt
Calendar: not_synced / synced / error / disabled
```

## Sincronização automática

Em `backend/app/routers/appointments.py`, ao criar ou atualizar um agendamento, se houver Google Calendar conectado, o sistema tenta sincronizar automaticamente.

Regras:

- se evento ainda não existe: cria evento Google;
- se já existe: atualiza evento Google;
- se status for `cancelado` e houver evento: remove/cancela evento no Google;
- se não houver conexão: não quebra a agenda interna.

## Testes feitos no sandbox

```txt
python -m py_compile backend/app/config.py backend/app/models.py backend/app/services/google_calendar_service.py backend/app/routers/calendar.py backend/app/routers/appointments.py backend/app/main.py
node --check frontend/js/api.js
node --check /tmp/configuracoes_inline.js
node --check /tmp/agenda_inline.js
OK: calendar state/tokens/model básico
```

## Como aplicar

Substitua/crie:

```txt
backend/app/config.py
backend/app/models.py
backend/app/main.py
backend/app/services/google_calendar_service.py
backend/app/routers/calendar.py
backend/app/routers/appointments.py
frontend/js/api.js
frontend/configuracoes.html
frontend/agenda.html
docs/GUIA_FASE_C2_3_GOOGLE_CALENDAR.md
```

Valide:

```powershell
python -m py_compile backend/app/config.py backend/app/models.py backend/app/services/google_calendar_service.py backend/app/routers/calendar.py backend/app/routers/appointments.py backend/app/main.py
node --check frontend/js/api.js
```

Commit:

```powershell
git add backend/app/config.py backend/app/models.py backend/app/main.py backend/app/services/google_calendar_service.py backend/app/routers/calendar.py backend/app/routers/appointments.py frontend/js/api.js frontend/configuracoes.html frontend/agenda.html docs/GUIA_FASE_C2_3_GOOGLE_CALENDAR.md
git commit -m "Adiciona Google Calendar OAuth e sync de agenda"
git push
```

## Teste em produção

1. Configurar env vars no Render.
2. Configurar OAuth Client no Google Cloud.
3. Abrir `/configuracoes.html`.
4. Clicar `Conectar Google Calendar`.
5. Autorizar conta Google.
6. Voltar para Configurações com sucesso.
7. Criar agendamento confirmado em `/agenda.html`.
8. Conferir se aparece no Google Calendar.
9. Alterar data/hora e conferir atualização.
10. Cancelar e conferir remoção/cancelamento.

## Observações importantes

- Essa é a primeira versão da integração.
- Ainda não há seleção de calendários além de `primary`.
- Ainda não há tela de logs de sincronização.
- O sync automático não deve quebrar a agenda interna se o Google falhar; ele marca erro no agendamento.
