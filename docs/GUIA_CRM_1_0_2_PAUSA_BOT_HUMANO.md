# Guia — CRM 1.0.2: Pausa do bot quando humano assume

## Objetivo

Complementar a trava de handoff humano para cobrir dois cenários reais:

1. O fluxo chegou no `+HUMANO` e o lead continua mandando mensagens.
2. O atendente humano assume manualmente pelo WhatsApp antes do fluxo terminar.
3. O operador pausa o bot manualmente pelo painel Leads.

## Problema resolvido

Antes, se o humano entrasse na conversa pelo WhatsApp enquanto o bot ainda estava conduzindo o fluxo, o bot continuava respondendo as próximas mensagens do lead.

Fluxo ruim:

```txt
Lead: Oi
Bot: Vamos fazer uma triagem...
Humano: Olá, vou assumir seu atendimento.
Lead: Obrigado.
Bot: Você já fez contato com suporte?
```

## Comportamento correto

Quando o humano envia mensagem manual pelo WhatsApp conectado, a Evolution envia evento com:

```txt
fromMe = true
```

Agora o dIAloga+ interpreta isso como:

```txt
humano assumiu atendimento
```

E faz:

```txt
lead.status = em_atendimento_humano
lead.stage = atendimento_manual
conversation.is_active = False
bot_paused = true
```

A partir disso, qualquer resposta do lead é apenas registrada. O bot não reinicia.

## Arquivos alterados

```txt
backend/app/services/lead_service.py
backend/app/routers/whatsapp_evolution.py
frontend/leads.html
```

## Recursos incluídos

### 1. Trava de handoff

Se o lead estiver em:

```txt
aguardando_humano
em_atendimento_humano
```

então o bot não responde novas mensagens.

### 2. Auto-pausa por mensagem manual do humano

Se a Evolution enviar mensagem com:

```txt
fromMe = true
```

e existir lead/conversa ativa para aquele telefone, o sistema pausa o bot automaticamente.

### 3. Pausar manualmente pelo painel

Na tela Leads foi adicionado botão:

```txt
⏸️ Pausar bot / assumir humano
```

Ele atualiza o lead para:

```txt
status = em_atendimento_humano
stage = atendimento_manual
```

## Testes feitos no sandbox

```txt
OK: auto-pausa fromMe + trava inbound posterior sem reiniciar bot
OK: leads.html atualizado para status humano
```

## Como aplicar

Substituir estes arquivos:

```txt
backend/app/services/lead_service.py
backend/app/routers/whatsapp_evolution.py
frontend/leads.html
docs/GUIA_CRM_1_0_2_PAUSA_BOT_HUMANO.md
```

Validar:

```powershell
python -m py_compile backend/app/services/lead_service.py backend/app/routers/whatsapp_evolution.py backend/app/routers/leads.py
node --check frontend/js/api.js
```

Commit:

```powershell
git add backend/app/services/lead_service.py backend/app/routers/whatsapp_evolution.py frontend/leads.html docs/GUIA_CRM_1_0_2_PAUSA_BOT_HUMANO.md
git commit -m "Adiciona pausa do bot para atendimento humano"
git push
```

## Testes em produção

### Teste A — fluxo chega no humano

1. Lead manda mensagem.
2. Bot segue até `+HUMANO`.
3. Lead manda nova mensagem.
4. Esperado: bot não responde.

### Teste B — humano assume antes do fim

1. Lead manda mensagem.
2. Bot começa fluxo.
3. Atendente responde manualmente pelo WhatsApp conectado.
4. Lead responde.
5. Esperado: bot não responde e não reinicia fluxo.

### Teste C — pausa pelo painel

1. Lead em andamento aparece em Leads.
2. Clicar no botão `⏸️`.
3. Lead fica como `Em atendimento humano`.
4. Lead manda nova mensagem.
5. Esperado: bot não responde.

## Próximo passo recomendado

Depois dessa correção, seguir para:

```txt
CRM 1.1 — Inbox Humano
```

A Inbox permitirá ver as mensagens registradas e responder pelo próprio dIAloga+.
