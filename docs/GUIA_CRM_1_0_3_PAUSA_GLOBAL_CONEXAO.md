# Guia — CRM 1.0.3: Pausa global por conexão WhatsApp

## Objetivo

Adicionar na tela **Configurações** um controle para pausar/retomar a automação de um número WhatsApp inteiro.

Essa pausa é diferente da pausa por lead:

| Tipo | Local | Escopo |
|---|---|---|
| Pausa por lead | Leads / futura Inbox | Apenas um contato |
| Pausa global | Configurações / conexão WhatsApp | Todos os contatos daquele número |

## Comportamento implementado

Quando uma conexão estiver com:

```txt
automation_paused = true
```

qualquer mensagem inbound recebida nessa conexão:

1. é registrada no CRM;
2. cria/reutiliza lead com origem `whatsapp_evolution`;
3. marca lead como `em_atendimento_humano`;
4. define stage `automacao_pausada`;
5. registra mensagem no histórico;
6. NÃO chama o `flow_engine`;
7. NÃO envia resposta automática.

## Arquivos alterados

```txt
backend/app/models_whatsapp.py
backend/app/database.py
backend/app/schemas_whatsapp.py
backend/app/routers/whatsapp_connections.py
backend/app/routers/whatsapp_evolution.py
frontend/js/api.js
frontend/configuracoes.html
```

## Nova coluna

Tabela:

```txt
whatsapp_connections
```

Coluna:

```txt
automation_paused BOOLEAN DEFAULT false
```

Adicionada via auto-migração aditiva em `database.py`.

## Novo endpoint

```txt
POST /api/whatsapp/connections/{conn_id}/automation-paused
```

Body:

```json
{
  "paused": true
}
```

ou:

```json
{
  "paused": false
}
```

## Frontend

Na tela:

```txt
frontend/configuracoes.html
```

A lista de conexões agora mostra:

```txt
Automação: ativa / pausada
```

E botão:

```txt
Pausar automação
Retomar automação
```

## Testes feitos no sandbox

```txt
OK: sintaxe e frontend limpos
OK: pausa global por conexão registra lead/mensagem e não aciona bot
OK: migration adiciona whatsapp_connections.automation_paused
```

## Como aplicar

Substitua estes arquivos:

```txt
backend/app/models_whatsapp.py
backend/app/database.py
backend/app/schemas_whatsapp.py
backend/app/routers/whatsapp_connections.py
backend/app/routers/whatsapp_evolution.py
frontend/js/api.js
frontend/configuracoes.html
docs/GUIA_CRM_1_0_3_PAUSA_GLOBAL_CONEXAO.md
```

Valide:

```powershell
python -m py_compile backend/app/models_whatsapp.py backend/app/database.py backend/app/schemas_whatsapp.py backend/app/routers/whatsapp_connections.py backend/app/routers/whatsapp_evolution.py backend/app/services/lead_service.py
node --check frontend/js/api.js
```

Commit:

```powershell
git add backend/app/models_whatsapp.py backend/app/database.py backend/app/schemas_whatsapp.py backend/app/routers/whatsapp_connections.py backend/app/routers/whatsapp_evolution.py frontend/js/api.js frontend/configuracoes.html docs/GUIA_CRM_1_0_3_PAUSA_GLOBAL_CONEXAO.md
git commit -m "Adiciona pausa global da automacao por conexao"
git push
```

## Teste em produção

1. Aguardar deploy backend e frontend.
2. Abrir Configurações.
3. Em Conexões cadastradas, clicar em `Pausar automação`.
4. Enviar mensagem de outro WhatsApp para o número conectado.
5. Esperado:
   - bot não responde;
   - lead aparece/atualiza em Leads;
   - origem `WhatsApp QR`;
   - status `Em atendimento humano`;
   - etapa `automacao_pausada`.
6. Voltar em Configurações e clicar em `Retomar automação`.
7. Novos atendimentos sem handoff individual voltam a acionar o bot.

## Observação importante

Mesmo com a automação global retomada, leads individuais em:

```txt
aguardando_humano
em_atendimento_humano
```

continuam com bot pausado individualmente. Isso é proposital.
