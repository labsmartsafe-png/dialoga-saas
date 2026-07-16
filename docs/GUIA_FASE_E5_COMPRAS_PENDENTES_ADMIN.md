# Guia — Fase E.5: Compras pendentes no Admin

## Objetivo

Permitir que o administrador veja e gerencie compras recebidas antes do cadastro do usuário.

Essa fase complementa a E.4:

- E.4 cria `PendingBillingAccount` quando webhook chega antes do cadastro;
- E.5 mostra essas compras no Admin e permite ação manual.

## Arquivos alterados

```txt
backend/app/routers/admin.py
frontend/js/api.js
frontend/admin.html
docs/GUIA_FASE_E5_COMPRAS_PENDENTES_ADMIN.md
```

## Novos endpoints Admin

### Listar compras pendentes

```txt
GET /api/admin/pending-billing?status=pending
```

Também permite outros status:

```txt
GET /api/admin/pending-billing?status=claimed
GET /api/admin/pending-billing?status=ignored
```

### Vincular compra pendente

```txt
POST /api/admin/pending-billing/{pending_id}/claim
```

Body opcional:

```json
{
  "user_id": 123
}
```

Se `user_id` não for enviado, o sistema tenta vincular pelo email comprador.

### Ignorar compra pendente

```txt
POST /api/admin/pending-billing/{pending_id}/ignore
```

Marca a compra como:

```txt
ignored
```

## Tela Admin

Em:

```txt
frontend/admin.html
```

Foi adicionada a seção:

```txt
Compras pendentes
```

Ela mostra:

```txt
email comprador
provedor
plano
produto
data
ações
```

Ações:

```txt
Vincular por email
Vincular por ID
Ignorar
```

## API JS

Adicionados em `frontend/js/api.js`:

```js
adminPendingBilling(qs)
adminClaimPendingBilling(id, body)
adminIgnorePendingBilling(id)
```

## Testes feitos no sandbox

```txt
python -m py_compile backend/app/routers/admin.py backend/app/services/billing_service.py backend/app/models.py
node --check frontend/js/api.js
node --check /tmp/admin_inline.js
OK: admin pending billing lista, vincula e ignora
```

## Como aplicar

Substitua:

```txt
backend/app/routers/admin.py
frontend/js/api.js
frontend/admin.html
docs/GUIA_FASE_E5_COMPRAS_PENDENTES_ADMIN.md
```

Valide:

```powershell
python -m py_compile backend/app/routers/admin.py backend/app/services/billing_service.py backend/app/models.py
node --check frontend/js/api.js
```

Commit:

```powershell
git add backend/app/routers/admin.py frontend/js/api.js frontend/admin.html docs/GUIA_FASE_E5_COMPRAS_PENDENTES_ADMIN.md
git commit -m "Adiciona compras pendentes no admin"
git push
```

## Teste em produção

1. Enviar webhook aprovado com email que ainda não existe no sistema.
2. Abrir `/admin.html`.
3. Verificar seção `Compras pendentes`.
4. Criar usuário com mesmo email ou usar um usuário existente.
5. Clicar `Vincular por email` ou `Vincular por ID`.
6. Confirmar que:

```txt
pending.status = claimed
user.plan = plano da compra
subscription.status = active
```

## Próximo passo recomendado

Fase E.6:

- envio de convite por email quando compra pendente chegar;
- ou ocultar link Admin para usuários não-admin;
- ou criar página de planos/upgrade dentro do produto.
