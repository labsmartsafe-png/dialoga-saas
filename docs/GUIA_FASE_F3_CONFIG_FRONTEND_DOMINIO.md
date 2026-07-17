# Guia — Fase F.3: Config central do frontend e preparação de domínio próprio

## Objetivo

Preparar o frontend para troca futura de domínio sem precisar editar manualmente todos os HTMLs.

Antes, várias páginas tinham:

```js
window.API_BASE = "https://dialoga-backend-1slr.onrender.com";
```

Isso dificulta migrar para domínio próprio.

Agora existe um arquivo central:

```txt
frontend/js/config.js
```

## Novo arquivo

```txt
frontend/js/config.js
```

Conteúdo principal:

```js
const DEFAULT_API_BASE = "https://dialoga-backend-1slr.onrender.com";
const DEFAULT_FRONTEND_BASE = "https://dialoga-frontend-8p28.onrender.com";

window.API_BASE = window.API_BASE || DEFAULT_API_BASE;
window.WF_PUBLIC_CONFIG = {
  apiBase: window.API_BASE,
  frontendBase: DEFAULT_FRONTEND_BASE,
  privacyUrl: DEFAULT_FRONTEND_BASE + "/privacidade.html",
  termsUrl: DEFAULT_FRONTEND_BASE + "/termos.html"
};
```

## Arquivos HTML alterados

Os HTMLs principais passaram a carregar:

```html
<script src="js/config.js"></script>
<script src="js/api.js"></script>
```

Arquivos atualizados:

```txt
frontend/admin.html
frontend/agenda.html
frontend/builder.html
frontend/configuracoes.html
frontend/dashboard.html
frontend/ia.html
frontend/inbox.html
frontend/leads.html
frontend/planos.html
frontend/setup.html
```

## Como trocar para domínio próprio no futuro

Quando migrar de Render para domínio próprio, alterar apenas:

```txt
frontend/js/config.js
```

De:

```js
const DEFAULT_API_BASE = "https://dialoga-backend-1slr.onrender.com";
const DEFAULT_FRONTEND_BASE = "https://dialoga-frontend-8p28.onrender.com";
```

Para algo como:

```js
const DEFAULT_API_BASE = "https://api.seudominio.com.br";
const DEFAULT_FRONTEND_BASE = "https://app.seudominio.com.br";
```

## Também será necessário alterar no Render backend

```env
PUBLIC_BASE_URL=https://api.seudominio.com.br
FRONTEND_BASE_URL=https://app.seudominio.com.br
CORS_ORIGINS=https://app.seudominio.com.br
GOOGLE_REDIRECT_URI=https://api.seudominio.com.br/api/calendar/google/callback
PRIVACY_POLICY_URL=https://app.seudominio.com.br/privacidade.html
TERMS_URL=https://app.seudominio.com.br/termos.html
```

## Também será necessário alterar no Google Cloud

Authorized JavaScript origins:

```txt
https://app.seudominio.com.br
```

Authorized redirect URIs:

```txt
https://api.seudominio.com.br/api/calendar/google/callback
```

## Também será necessário alterar na Meta

Webhook futuro:

```txt
https://api.seudominio.com.br/webhook/whatsapp/meta
```

Política de privacidade:

```txt
https://app.seudominio.com.br/privacidade.html
```

## Também será necessário alterar na Evolution

Novas conexões QR devem apontar para:

```txt
https://api.seudominio.com.br/webhook/whatsapp/evo
```

Atenção: conexões antigas podem continuar com webhook antigo. Pode ser necessário recriar ou atualizar instâncias.

## Validações feitas

```txt
node --check frontend/js/config.js
node --check frontend/js/api.js
OK: config central aplicado nos HTMLs principais
```

Também foi verificado que os HTMLs principais não contêm scripts externos injetados:

```txt
kaspersky
cloudflareinsights
cdn-cgi
challenge-platform
```

## Como aplicar

Substitua/crie:

```txt
frontend/js/config.js
frontend/admin.html
frontend/agenda.html
frontend/builder.html
frontend/configuracoes.html
frontend/dashboard.html
frontend/ia.html
frontend/inbox.html
frontend/leads.html
frontend/planos.html
frontend/setup.html
docs/GUIA_FASE_F3_CONFIG_FRONTEND_DOMINIO.md
```

Valide:

```powershell
node --check frontend/js/config.js
node --check frontend/js/api.js
```

Commit:

```powershell
git add frontend/js/config.js frontend/admin.html frontend/agenda.html frontend/builder.html frontend/configuracoes.html frontend/dashboard.html frontend/ia.html frontend/inbox.html frontend/leads.html frontend/planos.html frontend/setup.html docs/GUIA_FASE_F3_CONFIG_FRONTEND_DOMINIO.md
git commit -m "Centraliza configuracao publica do frontend"
git push
```

## Próximo passo recomendado

Depois desta fase, seguir para:

```txt
Fase F.4 — Checklist final de domínio próprio e variáveis de produção
```

Ou iniciar:

```txt
Fase E.8 — Página de assinaturas/upgrade mais integrada ao checkout
```
