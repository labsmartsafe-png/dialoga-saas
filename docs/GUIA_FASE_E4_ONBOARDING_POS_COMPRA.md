# Guia — Fase E.4: Onboarding pós-compra

## Objetivo

Melhorar o fluxo de billing quando o webhook da Hotmart/Eduzz chega **antes** do usuário se cadastrar no dIAloga+.

Antes:

```txt
Webhook aprovado chega
↓
Email comprador não existe em users
↓
Evento ignored
```

Agora:

```txt
Webhook aprovado chega
↓
Email comprador não existe em users
↓
Cria compra pendente
↓
Usuário se cadastra depois com o mesmo email
↓
Plano é aplicado automaticamente
```

## Arquivos alterados

```txt
backend/app/models.py
backend/app/services/billing_service.py
backend/app/routers/auth.py
backend/app/routers/admin.py
```

## Nova tabela

```txt
pending_billing_accounts
```

Campos:

```txt
id
provider
external_id
buyer_email
plan
status
product_name
raw_payload
claimed_user_id
created_at
claimed_at
```

Status:

```txt
pending
claimed
canceled
ignored
```

Como é tabela nova, `create_all()` cria automaticamente.

## Novo comportamento no webhook

Se o pagamento é aprovado e o email ainda não existe no sistema:

```txt
cria PendingBillingAccount
marca evento como processed
retorna pending=true
```

Exemplo de retorno:

```json
{
  "ok": true,
  "pending": true,
  "email": "cliente@email.com",
  "plan": "profissional",
  "pending_id": 1
}
```

## Novo comportamento no cadastro

Em:

```txt
POST /api/auth/register
```

Depois de criar o usuário, o sistema procura compra pendente com o mesmo email.

Se encontrar:

```txt
user.plan = plano pendente
user.is_active = true
AISettings.monthly_ai_limit = limite do plano
cria Subscription active
pending.status = claimed
```

## Fluxo recomendado por enquanto

1. Cliente compra na Hotmart/Eduzz.
2. Webhook chega ao dIAloga+.
3. Se usuário não existe, fica pendente.
4. Cliente se cadastra no dIAloga+ com o mesmo email da compra.
5. O sistema aplica o plano automaticamente.

## Limitação atual

Ainda não envia e-mail convite automaticamente.

Para isso será necessária uma fase futura com provedor de e-mail transacional:

```txt
Resend
SendGrid
Amazon SES
Mailgun
```

## Testes feitos no sandbox

```txt
python -m py_compile backend/app/models.py backend/app/services/billing_service.py backend/app/routers/billing.py backend/app/routers/auth.py backend/app/auth.py backend/app/routers/admin.py backend/app/main.py
OK: billing pendente é aplicado no cadastro
```

## Como aplicar

Substitua:

```txt
backend/app/models.py
backend/app/services/billing_service.py
backend/app/routers/auth.py
backend/app/routers/admin.py
docs/GUIA_FASE_E4_ONBOARDING_POS_COMPRA.md
```

Valide:

```powershell
python -m py_compile backend/app/models.py backend/app/services/billing_service.py backend/app/routers/billing.py backend/app/routers/auth.py backend/app/auth.py backend/app/routers/admin.py backend/app/main.py
```

Commit:

```powershell
git add backend/app/models.py backend/app/services/billing_service.py backend/app/routers/auth.py backend/app/routers/admin.py docs/GUIA_FASE_E4_ONBOARDING_POS_COMPRA.md
git commit -m "Adiciona onboarding pos compra com billing pendente"
git push
```

## Próximo passo recomendado

Fase E.5:

- tela Admin para ver compras pendentes;
- botão para vincular compra pendente manualmente;
- envio de convite por e-mail quando domínio/e-mail oficial estiver pronto.
