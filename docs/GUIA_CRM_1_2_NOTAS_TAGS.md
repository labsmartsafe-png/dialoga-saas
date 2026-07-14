# Guia — CRM 1.2: Notas internas e Tags

## Objetivo

Adicionar recursos básicos de CRM operacional à Inbox Humano:

- **Tags** para classificar leads;
- **Notas internas** que não são enviadas ao WhatsApp.

## Arquivos alterados/criados

```txt
backend/app/models.py
backend/app/database.py
backend/app/schemas.py
backend/app/routers/leads.py
backend/app/routers/inbox.py
frontend/js/api.js
frontend/inbox.html
frontend/leads.html
docs/GUIA_CRM_1_2_NOTAS_TAGS.md
```

## Banco de dados

### Nova coluna em `leads`

```txt
tags JSON
```

Adicionada via auto-migração aditiva em `database.py`.

### Nova tabela

```txt
lead_notes
```

Campos:

```txt
id
owner_id
lead_id
content
created_at
```

Observação: notas internas **não são enviadas ao WhatsApp**.

## Backend

### `LeadOut`

Agora retorna:

```txt
tags: list[str]
```

### `LeadUpdate`

Agora aceita:

```json
{
  "tags": ["urgente", "vip"]
}
```

### Novos endpoints em `/api/leads`

Listar notas:

```txt
GET /api/leads/{lead_id}/notes
```

Criar nota:

```txt
POST /api/leads/{lead_id}/notes
```

Body:

```json
{
  "content": "Cliente pediu retorno amanhã."
}
```

Excluir nota:

```txt
DELETE /api/leads/{lead_id}/notes/{note_id}
```

## Inbox

Na tela:

```txt
frontend/inbox.html
```

Agora aparece um bloco de CRM com:

- tags do lead;
- campo para adicionar tag;
- lista de notas internas;
- campo para adicionar nota.

## API JS

Adicionados métodos:

```js
listLeadNotes(leadId)
createLeadNote(leadId, body)
deleteLeadNote(leadId, noteId)
```

Também é usado `updateLead(leadId, { tags })` para atualizar tags.

## Testes feitos no sandbox

```txt
OK: migration tags idempotente
OK: tags e notas internas do lead funcionando
OK html clean
node --check frontend/js/api.js
node --check /tmp/inbox_inline.js
node --check /tmp/leads_inline.js
```

## Como aplicar

Substitua/adicione:

```txt
backend/app/models.py
backend/app/database.py
backend/app/schemas.py
backend/app/routers/leads.py
backend/app/routers/inbox.py
frontend/js/api.js
frontend/inbox.html
frontend/leads.html
docs/GUIA_CRM_1_2_NOTAS_TAGS.md
```

Valide:

```powershell
python -m py_compile backend/app/models.py backend/app/database.py backend/app/schemas.py backend/app/routers/leads.py backend/app/routers/inbox.py
node --check frontend/js/api.js
```

Commit:

```powershell
git add backend/app/models.py backend/app/database.py backend/app/schemas.py backend/app/routers/leads.py backend/app/routers/inbox.py frontend/js/api.js frontend/inbox.html frontend/leads.html docs/GUIA_CRM_1_2_NOTAS_TAGS.md
git commit -m "Adiciona notas internas e tags no CRM"
git push
```

## Teste em produção

1. Abrir `inbox.html`.
2. Selecionar um atendimento.
3. Adicionar uma tag, por exemplo:

```txt
urgente
```

4. Adicionar uma nota interna:

```txt
Cliente pediu retorno amanhã às 10h.
```

5. Atualizar a página e confirmar que tag/nota continuam salvas.

## Próximo passo recomendado

Após validar, seguir para uma destas opções:

1. Melhorar filtros por tags na Inbox e Leads;
2. Adicionar contador de mensagens não lidas real;
3. Fase B — Áudio no WhatsApp.
