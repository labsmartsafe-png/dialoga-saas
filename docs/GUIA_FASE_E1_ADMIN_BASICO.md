# Guia — Fase E.1: Painel Admin básico

## Objetivo

Criar uma área administrativa para o dono do SaaS acompanhar usuários/clientes e fazer gestão inicial de acesso/plano.

## Acesso Admin

Um usuário é considerado admin se:

1. `users.is_admin = true`; ou
2. o e-mail dele está na env var:

```env
ADMIN_EMAILS=admin@seudominio.com.br,voce@gmail.com
```

Essa abordagem permite liberar o primeiro admin sem editar o banco manualmente.

## Nova variável no Render

Adicionar no backend:

```env
ADMIN_EMAILS=seuemail@gmail.com
```

Pode ter múltiplos separados por vírgula.

## Nova coluna

Tabela:

```txt
users
```

Coluna:

```txt
is_admin BOOLEAN DEFAULT false
```

Adicionada via `_ADDITIVE_COLUMNS` em `backend/app/database.py`.

## Backend criado

```txt
backend/app/routers/admin.py
```

Prefixo:

```txt
/api/admin
```

Endpoints:

```txt
GET /api/admin/overview
GET /api/admin/users
PUT /api/admin/users/{user_id}
```

## O Admin permite

### Visão geral

Mostra totais:

```txt
usuários
usuários ativos
leads
leads reais
conexões WhatsApp
agendamentos
bases IA
conversas
```

### Lista de usuários

Para cada usuário mostra:

```txt
empresa
email
plano
ativo/inativo
admin/não admin
fluxos
leads
leads reais
conexões WhatsApp
agendamentos
bases IA
consumo IA mensal
criação
```

### Ações

```txt
ativar/desativar usuário
alterar plano manualmente
tornar/remover admin
```

Com proteção para evitar que o admin remova seu próprio acesso por acidente.

## Frontend criado

```txt
frontend/admin.html
```

## API JS alterada

Adicionados em `frontend/js/api.js`:

```js
adminOverview()
adminUsers(qs)
adminUpdateUser(id, body)
```

## Menus

Adicionado link:

```txt
Admin
```

nos menus principais.

Observação: nesta primeira versão o link aparece no menu, mas a API bloqueia não-admin com HTTP 403. Em fase futura, podemos ocultar o link no frontend com base em `user.is_admin`.

## Arquivos alterados/criados

```txt
backend/app/config.py
backend/app/models.py
backend/app/database.py
backend/app/schemas.py
backend/app/routers/admin.py
backend/app/main.py
frontend/js/api.js
frontend/admin.html
frontend/dashboard.html
frontend/setup.html
frontend/builder.html
frontend/leads.html
frontend/inbox.html
frontend/agenda.html
frontend/ia.html
frontend/configuracoes.html
docs/GUIA_FASE_E1_ADMIN_BASICO.md
```

## Testes feitos no sandbox

```txt
python -m py_compile backend/app/config.py backend/app/models.py backend/app/database.py backend/app/schemas.py backend/app/routers/admin.py backend/app/main.py
node --check frontend/js/api.js
node --check /tmp/admin_inline.js
OK html clean/menu admin
OK: admin overview/list/update funcionando
```

## Como aplicar

Substitua/crie os arquivos listados acima.

Valide:

```powershell
python -m py_compile backend/app/config.py backend/app/models.py backend/app/database.py backend/app/schemas.py backend/app/routers/admin.py backend/app/main.py
node --check frontend/js/api.js
```

Configure no Render:

```env
ADMIN_EMAILS=seuemail@gmail.com
```

Commit:

```powershell
git add backend/app/config.py backend/app/models.py backend/app/database.py backend/app/schemas.py backend/app/routers/admin.py backend/app/main.py frontend/js/api.js frontend/admin.html frontend/dashboard.html frontend/setup.html frontend/builder.html frontend/leads.html frontend/inbox.html frontend/agenda.html frontend/ia.html frontend/configuracoes.html docs/GUIA_FASE_E1_ADMIN_BASICO.md
git commit -m "Adiciona painel admin basico"
git push
```

## Teste em produção

1. Adicionar seu e-mail em `ADMIN_EMAILS` no Render.
2. Aguardar deploy.
3. Logar com esse e-mail.
4. Abrir:

```txt
/admin.html
```

5. Verificar overview.
6. Alterar plano de um usuário teste.
7. Desativar/ativar usuário teste.

## Próximos passos recomendados

1. Ocultar link Admin para usuários não-admin.
2. Adicionar tela de detalhes do usuário.
3. Ver consumo IA por período.
4. Integrar Hotmart/Eduzz para liberar acesso automaticamente.
5. Criar planos/limites reais.
