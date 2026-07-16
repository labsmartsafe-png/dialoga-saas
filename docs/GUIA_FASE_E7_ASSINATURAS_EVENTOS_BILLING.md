# Guia — Fase E.7: Assinaturas e eventos de billing no Admin

## Objetivo

Adicionar ao Painel Admin uma visão de auditoria para:

- assinaturas;
- eventos de webhook Hotmart/Eduzz;
- erros/ignorados/processados.

## Arquivos alterados

```txt
backend/app/routers/admin.py
frontend/js/api.js
frontend/admin.html
docs/GUIA_FASE_E7_ASSINATURAS_EVENTOS_BILLING.md
```

## Novos endpoints Admin

### Listar assinaturas

```txt
GET /api/admin/subscriptions
```

Filtros opcionais:

```txt
status
provider
```

Exemplo:

```txt
GET /api/admin/subscriptions?status=active
```

### Listar eventos de billing

```txt
GET /api/admin/billing-events
```

Filtros opcionais:

```txt
status
provider
```

Exemplo:

```txt
GET /api/admin/billing-events?status=failed
```

## Tela Admin

Em:

```txt
frontend/admin.html
```

Foram adicionadas seções:

```txt
Assinaturas
Eventos de Billing
```

### Assinaturas mostra

```txt
cliente
email
provedor
plano
status
produto
atualizado em
```

### Eventos mostra

```txt
quando
provedor
evento
email comprador
status
erro
external_event_id
```

## API JS

Adicionados em `frontend/js/api.js`:

```js
adminSubscriptions(qs)
adminBillingEvents(qs)
```

## Testes feitos no sandbox

```txt
python -m py_compile backend/app/routers/admin.py backend/app/models.py backend/app/main.py
node --check frontend/js/api.js
node --check /tmp/admin_inline.js
OK: admin assinaturas e eventos billing funcionando
```

## Como aplicar

Substitua:

```txt
backend/app/routers/admin.py
frontend/js/api.js
frontend/admin.html
docs/GUIA_FASE_E7_ASSINATURAS_EVENTOS_BILLING.md
```

Valide:

```powershell
python -m py_compile backend/app/routers/admin.py backend/app/models.py backend/app/main.py
node --check frontend/js/api.js
```

Commit:

```powershell
git add backend/app/routers/admin.py frontend/js/api.js frontend/admin.html docs/GUIA_FASE_E7_ASSINATURAS_EVENTOS_BILLING.md
git commit -m "Adiciona assinaturas e eventos de billing no admin"
git push
```

## Teste em produção

1. Abrir `/admin.html` como admin.
2. Conferir se aparecem as seções:
   - Compras pendentes;
   - Assinaturas;
   - Eventos de Billing.
3. Enviar webhook de teste Hotmart/Eduzz.
4. Verificar se o evento aparece em Eventos de Billing.
5. Se o usuário existir, verificar assinatura.
6. Se usuário não existir, verificar Compras pendentes.

## Próximo passo recomendado

- Criar filtros visuais por status/provedor nessas tabelas;
- Criar export CSV de billing;
- Preparar envio de convite por email quando domínio/e-mail oficial estiver pronto.
