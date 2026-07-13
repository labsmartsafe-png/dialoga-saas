# Guia — CRM 1.0.1: Trava de Handoff Humano

## Problema resolvido

Antes desta correção, quando o fluxo chegava em `+HUMANO`, a conversa automática era encerrada. Se depois o humano chamasse o lead pelo WhatsApp e o lead respondesse, o webhook recebia a mensagem, não encontrava conversa ativa e iniciava o fluxo do bot novamente.

Resultado indesejado:

```txt
Bot transfere para humano
Humano fala com lead
Lead responde
Bot reinicia fluxo do zero
```

## Comportamento correto

Se o lead estiver com status:

```txt
aguardando_humano
em_atendimento_humano
```

então qualquer nova mensagem do lead deve:

1. ser registrada no histórico;
2. atualizar `last_interaction_at`;
3. manter o status atual;
4. marcar o webhook como processado;
5. NÃO chamar `flow_engine.start_conversation`;
6. NÃO chamar `flow_engine.send_user_message`;
7. NÃO enviar resposta automática.

## Arquivos alterados

```txt
backend/app/services/lead_service.py
backend/app/routers/whatsapp_evolution.py
frontend/leads.html
```

## Alterações principais

### `lead_service.py`

Adicionado:

```python
STATUS_EM_ATENDIMENTO_HUMANO = "em_atendimento_humano"
HUMAN_HANDOFF_STATUSES = ("aguardando_humano", "em_atendimento_humano")
```

### `whatsapp_evolution.py`

Adicionado bloqueio antes de criar nova conversa:

```txt
se existe lead whatsapp_evolution do mesmo telefone/fluxo/conexão em status humano:
    registra inbound
    atualiza última interação
    não roda bot
```

### `leads.html`

Adicionado status visual:

```txt
Em atendimento humano
```

## Testes feitos no sandbox

```txt
OK: handoff lock registra inbound e não reinicia bot
OK: leads.html atualizado para status humano
```

## Como testar em produção

1. Envie uma mensagem para o WhatsApp conectado.
2. Complete o fluxo até cair no `+HUMANO`.
3. Confira em Leads que o status está `Aguardando humano`.
4. Pelo WhatsApp conectado, o humano envia uma mensagem manual para o lead.
5. O lead responde.
6. Resultado esperado:
   - o bot NÃO responde;
   - o fluxo NÃO reinicia;
   - a mensagem fica registrada no histórico para futura Inbox Humano;
   - lead continua aguardando/atendimento humano.

## Observação

Esta correção é uma trava operacional mínima. A próxima fase recomendada continua sendo:

```txt
CRM 1.1 — Inbox Humano
```

A Inbox Humano vai permitir ver essas mensagens registradas dentro do painel e responder pelo próprio dIAloga+.
