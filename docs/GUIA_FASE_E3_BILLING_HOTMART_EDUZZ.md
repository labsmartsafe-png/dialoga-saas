# Guia — Fase E.3: Billing webhooks Hotmart/Eduzz

## Objetivo

Preparar o dIAloga+ para liberar ou bloquear acesso automaticamente a partir de eventos de pagamento da Hotmart/Eduzz.

## Arquivos criados

```txt
backend/app/services/billing_service.py
backend/app/routers/billing.py
docs/GUIA_FASE_E3_BILLING_HOTMART_EDUZZ.md
```

## Arquivos alterados

```txt
backend/app/config.py
backend/app/models.py
backend/app/main.py
backend/app/routers/admin.py
```

## Novas variáveis no Render

```env
BILLING_ENABLED=true
BILLING_PROVIDER=hotmart
BILLING_DEFAULT_PLAN=profissional
HOTMART_WEBHOOK_TOKEN=<token secreto que voce definir>
EDUZZ_WEBHOOK_TOKEN=<token secreto que voce definir>
```

Observação: o token é definido por você e deve ser configurado também no painel da Hotmart/Eduzz quando configurar o webhook.

## Novas tabelas

### `subscriptions`

Registra assinatura/acesso por usuário.

Campos principais:

```txt
owner_id
provider
external_id
plan
status
buyer_email
product_name
raw_payload
started_at
canceled_at
```

### `billing_webhook_events`

Registra todos os eventos recebidos para auditoria/idempotência.

Campos principais:

```txt
provider
external_event_id
event_type
buyer_email
raw_payload
status
error
received_at
processed_at
```

## Novos endpoints públicos

### Hotmart

```txt
POST /api/billing/hotmart/webhook
```

### Eduzz

```txt
POST /api/billing/eduzz/webhook
```

## Autenticação do webhook

O backend aceita token por:

```txt
Authorization: Bearer <token>
```

ou headers:

```txt
X-Hotmart-Hottok
X-Eduzz-Token
X-Webhook-Token
```

ou query string:

```txt
?token=<token>
```

## Como o plano é identificado

O sistema tenta inferir plano pelo nome do produto/oferta:

```txt
performance -> performance
profissional/professional -> profissional
essencial/essential/basico -> essencial
```

Se não conseguir inferir, usa:

```env
BILLING_DEFAULT_PLAN
```

## O que acontece quando pagamento é aprovado

Se o email do comprador existir em `users.email`:

```txt
user.is_active = true
user.plan = plano inferido
AISettings.monthly_ai_limit = limite do plano
subscription.status = active
```

## O que acontece em cancelamento/reembolso/chargeback

```txt
user.is_active = false
subscription.status = canceled/refunded/chargeback/etc
```

## Eventos sem usuário correspondente

Se o e-mail comprador ainda não existe no sistema:

```txt
webhook fica como ignored
não cria usuário automaticamente nesta primeira versão
```

Isso é intencional para evitar criar contas sem senha/onboarding.

## Admin

O overview admin agora inclui:

```txt
subscriptions_total
subscriptions_active
```

## Testes feitos no sandbox

```txt
python -m py_compile backend/app/models.py backend/app/services/billing_service.py backend/app/routers/billing.py backend/app/main.py backend/app/routers/admin.py
OK: billing webhook ativa plano, idempotência e cancela
```

## Como aplicar

Substitua/crie:

```txt
backend/app/config.py
backend/app/models.py
backend/app/services/billing_service.py
backend/app/routers/billing.py
backend/app/main.py
backend/app/routers/admin.py
docs/GUIA_FASE_E3_BILLING_HOTMART_EDUZZ.md
```

Valide:

```powershell
python -m py_compile backend/app/models.py backend/app/services/billing_service.py backend/app/routers/billing.py backend/app/main.py backend/app/routers/admin.py
```

Commit:

```powershell
git add backend/app/config.py backend/app/models.py backend/app/services/billing_service.py backend/app/routers/billing.py backend/app/main.py backend/app/routers/admin.py docs/GUIA_FASE_E3_BILLING_HOTMART_EDUZZ.md
git commit -m "Adiciona webhooks de billing Hotmart Eduzz"
git push
```

## Configuração Hotmart/Eduzz

Configurar o webhook apontando para:

```txt
https://dialoga-backend-1slr.onrender.com/api/billing/hotmart/webhook?token=SEU_TOKEN
```

ou:

```txt
https://dialoga-backend-1slr.onrender.com/api/billing/eduzz/webhook?token=SEU_TOKEN
```

Quando migrar para domínio próprio:

```txt
https://api.seudominio.com.br/api/billing/hotmart/webhook?token=SEU_TOKEN
```

## Limitação atual

Esta fase não cria usuário automaticamente. Ela atualiza usuário existente pelo email.

Fluxo recomendado por enquanto:

1. Usuário se cadastra no dIAloga+ com o mesmo email da compra;
2. Hotmart/Eduzz envia webhook aprovado;
3. Sistema ativa usuário e ajusta plano.

## Próximo passo recomendado

Fase E.4:

- criar convite/onboarding pós-compra;
- ou criar usuário pendente automaticamente;
- ou integrar checkout com cadastro;
- tela admin de assinaturas e eventos de billing.
