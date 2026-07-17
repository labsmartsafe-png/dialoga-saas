# Guia — UX 1.1: App Shell moderno no Dashboard

## Objetivo

Iniciar a modernização visual do dIAloga+ trocando o menu horizontal antigo por uma estrutura de SaaS mais moderna com:

- sidebar lateral;
- topbar fixa;
- grupos de navegação;
- área de conteúdo padronizada;
- suporte a dark mode;
- visibilidade de Admin por permissão.

Nesta primeira etapa, a aplicação do novo layout foi feita apenas no Dashboard para validar a abordagem sem quebrar todas as telas de uma vez.

## Arquivos criados

```txt
frontend/js/layout.js
frontend/css/app-shell.css
docs/GUIA_UX1_APP_SHELL_DASHBOARD.md
```

## Arquivo alterado

```txt
frontend/dashboard.html
```

## Novo layout

A estrutura visual passa a ser:

```txt
┌──────────── Sidebar ────────────┬──────────── Topbar ────────────┐
│ dIAloga+                        │ Dashboard + ações              │
│                                 ├────────────────────────────────┤
│ Principal                       │ Conteúdo                        │
│ - Dashboard                     │ cards, métricas, tabelas        │
│ - Setup                         │                                 │
│                                 │                                 │
│ Atendimento                     │                                 │
│ - Leads                         │                                 │
│ - Inbox                         │                                 │
│ - Agenda                        │                                 │
│                                 │                                 │
│ Automação                       │                                 │
│ - Fluxos                        │                                 │
│ - IA / Conhecimento             │                                 │
│                                 │                                 │
│ Comercial                       │                                 │
│ - Planos                        │                                 │
│                                 │                                 │
│ Sistema                         │                                 │
│ - Configurações                 │                                 │
│ - Admin                         │                                 │
└─────────────────────────────────┴────────────────────────────────┘
```

## Arquivo `layout.js`

Novo arquivo:

```txt
frontend/js/layout.js
```

Ele cria funções:

```js
WFLayout.render({ active, title, subtitle, actionsHtml })
WFLayout.renderSidebar(active)
WFLayout.renderTopbar(options)
```

O link Admin continua com:

```html
data-admin-only
```

Então só aparece para admin após `WFAuth.applyRoleVisibility(user)`.

## Arquivo `app-shell.css`

Novo arquivo:

```txt
frontend/css/app-shell.css
```

Define:

- `.app-shell`
- `.shell-sidebar`
- `.shell-topbar`
- `.shell-content`
- `.shell-link`
- dark mode;
- responsividade para telas menores.

## Dashboard

`frontend/dashboard.html` agora usa:

```html
<link rel="stylesheet" href="css/app-shell.css">
<script src="js/layout.js"></script>
```

E renderiza o layout com:

```js
WFLayout.render({
  active: "dashboard",
  title: "Dashboard",
  subtitle: "Visão geral da sua operação, ROI, agenda e performance.",
  actionsHtml: '...'
});
```

## Testes feitos

```txt
node --check frontend/js/layout.js
node --check frontend/js/api.js
node --check frontend/js/auth.js
node --check frontend/js/config.js
node --check /tmp/dashboard_inline.js
OK dashboard shell
OK clean
```

Também foi validado que não há scripts externos injetados:

```txt
kaspersky
cloudflareinsights
cdn-cgi
challenge-platform
```

## Como aplicar

Substitua/crie:

```txt
frontend/js/layout.js
frontend/css/app-shell.css
frontend/dashboard.html
docs/GUIA_UX1_APP_SHELL_DASHBOARD.md
```

Valide:

```powershell
node --check frontend/js/layout.js
node --check frontend/js/api.js
node --check frontend/js/auth.js
node --check frontend/js/config.js
```

Commit:

```powershell
git add frontend/js/layout.js frontend/css/app-shell.css frontend/dashboard.html docs/GUIA_UX1_APP_SHELL_DASHBOARD.md
git commit -m "Adiciona app shell moderno no dashboard"
git push
```

## Teste em produção

1. Abrir `/dashboard.html`.
2. Confirmar sidebar lateral.
3. Confirmar topbar.
4. Confirmar que métricas carregam.
5. Confirmar que o link Admin aparece apenas para admin.
6. Testar dark mode.
7. Testar responsividade em tela menor.

## Próximo passo recomendado

Se o Dashboard estiver aprovado, aplicar o App Shell gradualmente em:

1. `inbox.html`
2. `leads.html`
3. `agenda.html`
4. `setup.html`
5. `builder.html`
6. `ia.html`
7. `configuracoes.html`
8. `planos.html`
9. `admin.html`

A recomendação é migrar uma ou duas telas por vez, testando a cada etapa.
