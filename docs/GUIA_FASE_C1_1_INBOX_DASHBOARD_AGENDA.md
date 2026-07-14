# Guia — Fase C.1.1/C.1.2: Agenda integrada à Inbox e Dashboard

## Objetivo

Aprimorar a Agenda interna com dois atalhos operacionais:

1. Criar agendamento a partir da Inbox Humano com o lead já pré-selecionado.
2. Mostrar próximos agendamentos no Dashboard.

## Arquivos alterados

```txt
frontend/inbox.html
frontend/agenda.html
frontend/dashboard.html
```

## Inbox → Agenda

Na tela:

```txt
frontend/inbox.html
```

Foi adicionado botão:

```txt
Agendar
```

Ao clicar, o usuário é enviado para:

```txt
agenda.html?lead_id=<id_do_lead>
```

## Agenda com lead pré-selecionado

Na tela:

```txt
frontend/agenda.html
```

Agora ela lê o parâmetro:

```txt
lead_id
```

Exemplo:

```txt
agenda.html?lead_id=123
```

E já seleciona o lead no formulário de novo agendamento.

Também preenche um título inicial:

```txt
Agendamento - Nome do lead
```

## Dashboard

Na tela:

```txt
frontend/dashboard.html
```

Foi adicionado card:

```txt
Próximos agendamentos
```

Ele lista os próximos agendamentos dos próximos 7 dias, usando:

```js
WFApi.listAppointments()
```

## Testes feitos

```txt
OK html clean
node --check /tmp/inbox_inline.js
node --check /tmp/agenda_inline.js
node --check /tmp/dashboard_inline.js
node --check frontend/js/api.js
python -m py_compile backend/app/routers/appointments.py backend/app/main.py
```

## Como aplicar

Substitua:

```txt
frontend/inbox.html
frontend/agenda.html
frontend/dashboard.html
docs/GUIA_FASE_C1_1_INBOX_DASHBOARD_AGENDA.md
```

Valide:

```powershell
node --check frontend/js/api.js
```

Commit:

```powershell
git add frontend/inbox.html frontend/agenda.html frontend/dashboard.html docs/GUIA_FASE_C1_1_INBOX_DASHBOARD_AGENDA.md
git commit -m "Integra agenda com Inbox e Dashboard"
git push
```

## Teste em produção

1. Abrir `/inbox.html`.
2. Selecionar um atendimento.
3. Clicar em `Agendar`.
4. Confirmar que `/agenda.html` abriu com o lead selecionado.
5. Criar o agendamento.
6. Abrir `/dashboard.html`.
7. Confirmar se o card `Próximos agendamentos` exibe o novo agendamento.
