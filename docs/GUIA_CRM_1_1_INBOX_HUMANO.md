# Guia — CRM 1.1: Inbox Humano

## Objetivo

Criar a primeira versão da **Inbox Humano** do dIAloga+, permitindo que o operador veja atendimentos pausados para humano e responda pelo próprio painel.

Esta fase usa a base já criada nas fases anteriores:

- `aguardando_humano`
- `em_atendimento_humano`
- pausa por lead
- pausa automática quando humano responde manualmente
- pausa global por conexão

## Arquivos criados

```txt
backend/app/routers/inbox.py
frontend/inbox.html
docs/GUIA_CRM_1_1_INBOX_HUMANO.md
```

## Arquivos alterados

```txt
backend/app/main.py
frontend/js/api.js
frontend/leads.html
frontend/configuracoes.html
```

## Endpoints novos

Prefixo:

```txt
/api/inbox
```

### Listar atendimentos

```txt
GET /api/inbox/conversations
```

Opcional:

```txt
GET /api/inbox/conversations?status=aguardando_humano
GET /api/inbox/conversations?status=em_atendimento_humano
```

### Detalhar conversa

```txt
GET /api/inbox/conversations/{lead_id}
```

### Assumir atendimento

```txt
POST /api/inbox/conversations/{lead_id}/assume
```

Marca:

```txt
status = em_atendimento_humano
stage = atendimento_manual
bot_paused = true
```

### Enviar mensagem humana

```txt
POST /api/inbox/conversations/{lead_id}/send
```

Body:

```json
{
  "text": "Olá, vou seguir com seu atendimento."
}
```

Envia via Evolution API e registra no histórico como:

```txt
sender = human
message_type = text_manual_panel
```

### Encerrar atendimento

```txt
POST /api/inbox/conversations/{lead_id}/close
```

Marca:

```txt
status = encerrado
stage = atendimento_encerrado
```

## Tela nova

```txt
frontend/inbox.html
```

Funcionalidades:

- listar atendimentos humanos;
- filtrar por `Aguardando` ou `Em atendimento`;
- ver histórico de mensagens;
- ver contexto capturado;
- assumir atendimento;
- enviar mensagem humana;
- encerrar atendimento.

## Alterações no menu

Foram adicionados links para:

```txt
Inbox
```

em:

```txt
frontend/leads.html
frontend/configuracoes.html
frontend/inbox.html
```

## API JS

Adicionados métodos em `frontend/js/api.js`:

```js
inboxList(qs)
inboxGet(leadId)
inboxAssume(leadId)
inboxSend(leadId, body)
inboxClose(leadId)
```

## Testes feitos no sandbox

```txt
OK: inbox files clean
OK: Inbox lista, assume e encerra atendimento
```

Também foi validado:

```txt
python -m py_compile backend/app/routers/inbox.py backend/app/main.py
node --check frontend/js/api.js
node --check /tmp/inbox_inline.js
```

## Como aplicar

Substitua/crie os arquivos:

```txt
backend/app/routers/inbox.py
backend/app/main.py
frontend/js/api.js
frontend/inbox.html
frontend/leads.html
frontend/configuracoes.html
docs/GUIA_CRM_1_1_INBOX_HUMANO.md
```

Valide:

```powershell
python -m py_compile backend/app/routers/inbox.py backend/app/main.py
node --check frontend/js/api.js
```

Commit:

```powershell
git add backend/app/routers/inbox.py backend/app/main.py frontend/js/api.js frontend/inbox.html frontend/leads.html frontend/configuracoes.html docs/GUIA_CRM_1_1_INBOX_HUMANO.md
git commit -m "Implementa Inbox Humano CRM 1.1"
git push
```

## Teste em produção

1. Criar ou usar um lead que esteja em:

```txt
aguardando_humano
```

ou:

```txt
em_atendimento_humano
```

2. Abrir:

```txt
https://dialoga-frontend-8p28.onrender.com/inbox.html
```

3. Selecionar o atendimento.
4. Clicar em `Assumir`.
5. Enviar uma mensagem pelo painel.
6. Confirmar no WhatsApp do lead que a mensagem chegou.
7. Confirmar que a mensagem aparece no histórico.
8. Clicar em `Encerrar`.

## Observação importante

Esta é a primeira versão da Inbox. Ela ainda não tem:

- múltiplos operadores;
- notas internas;
- tags;
- anexos;
- áudio;
- controle de leitura;
- SLA.

Esses pontos entram em fases futuras.
