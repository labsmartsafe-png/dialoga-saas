# Guia — Fase E.6: Planos + Admin oculto por permissão

## Objetivo

Melhorar a experiência de navegação e preparar visualmente o produto para upgrades de plano.

Esta fase combina:

1. Ocultar o link `Admin` para usuários não-admin.
2. Criar a tela `Planos` com limites, preços e links de checkout.

## Arquivos criados

```txt
backend/app/routers/plans.py
frontend/planos.html
docs/GUIA_FASE_E6_PLANOS_UX.md
```

## Arquivos alterados

```txt
backend/app/config.py
backend/app/main.py
frontend/js/api.js
frontend/js/auth.js
frontend/dashboard.html
frontend/setup.html
frontend/builder.html
frontend/leads.html
frontend/inbox.html
frontend/agenda.html
frontend/ia.html
frontend/configuracoes.html
frontend/admin.html
```

## Backend

### Novo endpoint

```txt
GET /api/plans
```

Retorna:

```txt
current_plan
plans[]
```

Cada plano inclui:

```txt
id
name
price_brl
description
limits
checkout_url
current
```

## Novas configurações opcionais no Render

Para botões de checkout:

```env
HOTMART_ESSENCIAL_URL=
HOTMART_PROFISSIONAL_URL=
HOTMART_PERFORMANCE_URL=
EDUZZ_ESSENCIAL_URL=
EDUZZ_PROFISSIONAL_URL=
EDUZZ_PERFORMANCE_URL=
```

Se `BILLING_PROVIDER=eduzz`, usa os links Eduzz.
Caso contrário, usa Hotmart.

Se a URL não estiver configurada, o botão mostra mensagem para falar com suporte.

## Frontend

### Nova tela

```txt
frontend/planos.html
```

Mostra:

- plano atual;
- preço;
- limite de fluxos;
- limite de conexões WhatsApp;
- limite de bases IA;
- limite de IA/mês;
- botão `Quero este plano`.

### Menu

Foi adicionado:

```txt
Planos
```

em todos os menus principais.

### Admin oculto para não-admin

Em `frontend/js/auth.js` foi adicionada função:

```js
applyRoleVisibility(user)
```

Ela esconde elementos com:

```html
[data-admin-only]
```

O link Admin agora tem:

```html
<a href="admin.html" data-admin-only style="display:none">Admin</a>
```

Se `user.is_admin = true`, ele aparece.

Importante: a segurança real continua no backend com HTTP 403.

## API JS

Adicionado:

```js
listPlans()
```

## Testes feitos no sandbox

```txt
python -m py_compile backend/app/config.py backend/app/routers/plans.py backend/app/main.py
node --check frontend/js/api.js
node --check /tmp/planos_inline.js
node --check /tmp/dashboard_inline.js
node --check /tmp/admin_inline.js
node --check /tmp/setup_inline.js
OK html clean menus role
OK: planos endpoint com checkout e plano atual
```

## Como aplicar

Substitua/crie:

```txt
backend/app/config.py
backend/app/routers/plans.py
backend/app/main.py
frontend/js/api.js
frontend/js/auth.js
frontend/planos.html
frontend/dashboard.html
frontend/setup.html
frontend/builder.html
frontend/leads.html
frontend/inbox.html
frontend/agenda.html
frontend/ia.html
frontend/configuracoes.html
frontend/admin.html
docs/GUIA_FASE_E6_PLANOS_UX.md
```

Valide:

```powershell
python -m py_compile backend/app/config.py backend/app/routers/plans.py backend/app/main.py
node --check frontend/js/api.js
```

Commit:

```powershell
git add backend/app/config.py backend/app/routers/plans.py backend/app/main.py frontend/js/api.js frontend/js/auth.js frontend/planos.html frontend/dashboard.html frontend/setup.html frontend/builder.html frontend/leads.html frontend/inbox.html frontend/agenda.html frontend/ia.html frontend/configuracoes.html frontend/admin.html docs/GUIA_FASE_E6_PLANOS_UX.md
git commit -m "Adiciona tela de planos e oculta admin por permissao"
git push
```

## Teste em produção

1. Logar como usuário admin.
2. Confirmar que o menu `Admin` aparece.
3. Logar como usuário comum.
4. Confirmar que o menu `Admin` não aparece.
5. Abrir `/planos.html`.
6. Conferir plano atual e limites.
7. Se URLs de checkout estiverem configuradas, clicar em `Quero este plano`.

## Próximo passo recomendado

Fase E.7:

- página pública/comercial simples;
- ou checkout + cadastro mais integrado;
- ou tela Admin de assinaturas e eventos de billing.
