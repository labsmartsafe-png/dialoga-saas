# Guia de aplicação — Fase CRM 1.0 do dIAloga+

## Objetivo

Implementar uma base global de Leads/CRM para separar e atualizar corretamente leads vindos de:

- `simulator`
- `whatsapp_evolution`
- `whatsapp_meta` no futuro
- manual/import/api no futuro

## Arquivos criados/alterados

### Novo arquivo

```txt
backend/app/services/lead_service.py
```

### Arquivos alterados

```txt
backend/app/models.py
backend/app/database.py
backend/app/schemas.py
backend/app/services/flow_engine.py
backend/app/routers/whatsapp_evolution.py
backend/app/routers/leads.py
frontend/leads.html
```

## O que muda

1. Cria serviço central de CRM:

```txt
lead_service.py
```

2. Adiciona colunas aditivas em `leads`:

```txt
conversation_id
connection_id
last_interaction_at
updated_at
```

3. Padroniza fontes:

```txt
simulator
whatsapp_evolution
whatsapp_meta
```

4. WhatsApp QR/Evolution passa a criar lead como:

```txt
source = whatsapp_evolution
connection_id = id da conexão QR
conversation_id = id da conversa
```

5. `+INPUT` e `+PERG` atualizam o contexto do lead.

6. `+HUMANO` muda status para:

```txt
aguardando_humano
```

7. `+FIM` muda status para:

```txt
encerrado
```

8. Tela Leads passa a ter filtro por origem:

```txt
Todas origens
Somente reais
Simulador
WhatsApp QR
WhatsApp Oficial
```

## Validações feitas no sandbox

```txt
OK: sintaxe Python/JS e leads.html sem scripts externos
OK: auto-migração CRM adiciona colunas em leads antigo
OK: CRM cria lead WhatsApp QR, preserva source e atualiza contexto/status até +HUMANO
OK: HTMLs sem scripts externos injetados; JS inline de leads válido
```

## Comandos para aplicar no projeto local

Depois de substituir os arquivos, rode:

```powershell
python -m py_compile backend/app/models.py backend/app/database.py backend/app/schemas.py backend/app/services/lead_service.py backend/app/services/flow_engine.py backend/app/routers/leads.py backend/app/routers/whatsapp_evolution.py
node --check frontend/js/api.js
```

Depois:

```powershell
git status
git add backend/app/models.py backend/app/database.py backend/app/schemas.py backend/app/services/lead_service.py backend/app/services/flow_engine.py backend/app/routers/whatsapp_evolution.py backend/app/routers/leads.py frontend/leads.html docs/GUIA_CRM_1_0_APLICACAO.md
git commit -m "Implementa CRM 1.0 com leads por origem"
git push
```

## Teste em produção depois do deploy

1. Aguardar `Deploy live` no Render.
2. Abrir:

```txt
https://dialoga-frontend-8p28.onrender.com/leads.html
```

3. Dar `Ctrl + F5`.
4. Enviar nova mensagem para o WhatsApp conectado via QR.
5. Verificar se aparece lead em Leads com origem:

```txt
WhatsApp QR
```

6. Responder o fluxo até o `+HUMANO`.
7. Verificar se status ficou:

```txt
Aguardando humano
```

## Observação

Conversas antigas podem não aparecer automaticamente com todos os novos campos. O teste correto é iniciar uma nova conversa/mensagem após o deploy.
