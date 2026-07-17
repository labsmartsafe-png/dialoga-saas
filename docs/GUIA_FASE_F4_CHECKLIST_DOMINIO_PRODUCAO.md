# Guia — Fase F.4: Checklist final de domínio próprio e variáveis de produção

## Objetivo

Centralizar tudo que precisa ser alterado quando o dIAloga+ sair do ambiente Render/onrender/teste e migrar para domínio próprio e operação comercial.

Este guia deve ser usado antes do go-live.

---

## 1. Domínios recomendados

Hoje o projeto usa:

```txt
Backend:  https://dialoga-backend-1slr.onrender.com
Frontend: https://dialoga-frontend-8p28.onrender.com
```

Para produção, recomenda-se:

```txt
Backend/API: https://api.seudominio.com.br
Frontend/App: https://app.seudominio.com.br
Site público: https://seudominio.com.br
```

Exemplo:

```txt
https://api.dialogamais.com.br
https://app.dialogamais.com.br
https://dialogamais.com.br
```

---

## 2. Render — variáveis de ambiente do backend

Atualizar no serviço backend:

```env
APP_ENV=production
DEBUG=false
PUBLIC_BASE_URL=https://api.seudominio.com.br
FRONTEND_BASE_URL=https://app.seudominio.com.br
CORS_ORIGINS=https://app.seudominio.com.br,https://seudominio.com.br
PRIVACY_POLICY_URL=https://app.seudominio.com.br/privacidade.html
TERMS_URL=https://app.seudominio.com.br/termos.html
```

### Segurança

Trocar/confirmar:

```env
SECRET_KEY=<secret forte, não padrão>
WA_FERNET_KEYS=<chave fernet com backup seguro>
ADMIN_EMAILS=admin@seudominio.com.br
```

Gerar Fernet:

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Importante: faça backup de `WA_FERNET_KEYS`. Se perder, tokens criptografados não poderão ser recuperados.

---

## 3. Frontend — config central

Arquivo:

```txt
frontend/js/config.js
```

Trocar:

```js
const DEFAULT_API_BASE = "https://dialoga-backend-1slr.onrender.com";
const DEFAULT_FRONTEND_BASE = "https://dialoga-frontend-8p28.onrender.com";
```

Para:

```js
const DEFAULT_API_BASE = "https://api.seudominio.com.br";
const DEFAULT_FRONTEND_BASE = "https://app.seudominio.com.br";
```

Depois validar:

```powershell
node --check frontend/js/config.js
node --check frontend/js/api.js
```

---

## 4. Google Cloud OAuth

### OAuth Consent Screen

Atualizar:

```txt
App name: dIAloga+
Support email: suporte@seudominio.com.br
Developer contact: dev/admin@seudominio.com.br
Authorized domain: seudominio.com.br
Privacy policy: https://app.seudominio.com.br/privacidade.html
Terms: https://app.seudominio.com.br/termos.html
```

### OAuth Client — Web Application

Authorized JavaScript origins:

```txt
https://app.seudominio.com.br
```

Authorized redirect URIs:

```txt
https://api.seudominio.com.br/api/calendar/google/callback
```

Atualizar no Render:

```env
GOOGLE_REDIRECT_URI=https://api.seudominio.com.br/api/calendar/google/callback
```

### Publicação/verificação

Enquanto o app estiver em modo teste, apenas test users conseguem conectar.

Para clientes reais:

- publicar app OAuth;
- configurar domínio próprio;
- políticas e termos oficiais;
- verificar app, se o Google exigir.

---

## 5. Meta Cloud API

Atualizar no Meta App:

### Webhook Callback URL

```txt
https://api.seudominio.com.br/webhook/whatsapp/meta
```

### Verify token

Manter ou trocar:

```env
WHATSAPP_VERIFY_TOKEN=dialoga-verify
```

### App domains

Adicionar:

```txt
seudominio.com.br
api.seudominio.com.br
app.seudominio.com.br
```

### URLs legais

```txt
Privacy Policy: https://app.seudominio.com.br/privacidade.html
Terms: https://app.seudominio.com.br/termos.html
```

### Business Verification

Obrigatório para produção séria e para resolver restrições de envio no Brasil, como erro:

```txt
130497 — Business account restricted from messaging users in this country
```

---

## 6. Evolution API / WhatsApp QR

Novas conexões QR devem usar webhook novo:

```txt
https://api.seudominio.com.br/webhook/whatsapp/evo
```

Isso depende de:

```env
PUBLIC_BASE_URL=https://api.seudominio.com.br
```

Atenção:

- Instâncias Evolution antigas podem continuar apontando para o domínio antigo.
- Se necessário, recriar conexão QR ou atualizar webhook da instância na Evolution.
- Manter aviso de risco de banimento para método QR/não-oficial.

---

## 7. Billing Hotmart/Eduzz

Atualizar URLs de webhook nos provedores:

### Hotmart

```txt
https://api.seudominio.com.br/api/billing/hotmart/webhook?token=SEU_TOKEN
```

### Eduzz

```txt
https://api.seudominio.com.br/api/billing/eduzz/webhook?token=SEU_TOKEN
```

Render:

```env
BILLING_ENABLED=true
BILLING_PROVIDER=hotmart
BILLING_DEFAULT_PLAN=profissional
HOTMART_WEBHOOK_TOKEN=<token forte>
EDUZZ_WEBHOOK_TOKEN=<token forte>
```

URLs de checkout:

```env
HOTMART_ESSENCIAL_URL=
HOTMART_PROFISSIONAL_URL=
HOTMART_PERFORMANCE_URL=
EDUZZ_ESSENCIAL_URL=
EDUZZ_PROFISSIONAL_URL=
EDUZZ_PERFORMANCE_URL=
```

---

## 8. Gemini / IA

Antes de uso comercial:

```env
GEMINI_API_KEY=<key com billing ativo>
GEMINI_CHAT_MODEL=gemini-2.5-flash
```

Avaliar custo:

- `gemini-2.5-flash` para qualidade;
- `gemini-2.5-flash-lite` para custo menor;
- BYOK no futuro;
- créditos/limite por plano.

Importante:

```txt
Free tier não deve ser usado comercialmente.
```

---

## 9. Render plano pago

O plano Free:

- dorme por inatividade;
- causa cold start;
- pode estourar memória;
- prejudica webhooks do WhatsApp;
- prejudica experiência comercial.

Antes de go-live:

```txt
Migrar backend para plano pago.
```

Também avaliar:

- logs;
- monitoramento;
- alertas;
- backups Neon.

---

## 10. E-mails oficiais

Todos os e-mails atuais são temporários.

Configurar e-mails oficiais:

```txt
suporte@seudominio.com.br
contato@seudominio.com.br
admin@seudominio.com.br
no-reply@seudominio.com.br
```

Configurar DNS:

```txt
SPF
DKIM
DMARC
```

Escolher provedor transacional:

```txt
Resend
SendGrid
Amazon SES
Mailgun
```

Futuras env vars:

```env
EMAIL_FROM=no-reply@seudominio.com.br
SUPPORT_EMAIL=suporte@seudominio.com.br
SMTP_HOST=
SMTP_USER=
SMTP_PASSWORD=
```

---

## 11. Arquivos/pontos internos a atualizar

### Frontend

```txt
frontend/js/config.js
frontend/privacidade.html
frontend/termos.html
```

### Backend

```txt
backend/app/config.py
Render Environment
Google Cloud OAuth
Meta App
Hotmart/Eduzz webhooks
Evolution webhook/base URL
```

### Documentação

Substituir referências antigas em docs se necessário:

```txt
dialoga-backend-1slr.onrender.com
dialoga-frontend-8p28.onrender.com
labsmartsafe@gmail.com
```

---

## 12. Checklist de validação pós-migração

Depois de trocar para domínio próprio:

```txt
[ ] Login funciona
[ ] Dashboard carrega
[ ] Builder carrega
[ ] Setup cria fluxo
[ ] IA/RAG indexa e responde
[ ] WhatsApp QR conecta
[ ] Webhook Evolution chega no novo domínio
[ ] Bot responde no WhatsApp
[ ] Inbox envia mensagem humana
[ ] Áudio transcreve
[ ] Agenda interna funciona
[ ] Google Calendar conecta no novo redirect
[ ] Agendamento sincroniza com Google
[ ] Billing webhook chega no novo domínio
[ ] Admin abre apenas para admin
[ ] Planos exibem URLs de checkout
[ ] Privacidade/Termos abrem no domínio oficial
[ ] Meta webhook verifica
[ ] CORS não bloqueia frontend
```

---

## 13. Checklist de go-live comercial

Antes de vender:

```txt
[ ] Domínio próprio configurado
[ ] E-mails oficiais configurados
[ ] Política de privacidade revisada
[ ] Termos de uso revisados
[ ] Render backend pago
[ ] Gemini billing ativo
[ ] Meta Business Verification iniciada/concluída
[ ] Google OAuth publicado/verificado se necessário
[ ] Hotmart/Eduzz configurado
[ ] Painel Admin testado
[ ] Backup do WA_FERNET_KEYS feito
[ ] Backup/monitoramento Neon definido
[ ] Aviso de risco do WhatsApp QR visível nos termos/oferta
[ ] Planos e limites validados
[ ] Fluxos por nicho testados
[ ] Onboarding Setup testado
```

---

## 14. Próximo passo recomendado

Depois deste checklist, a próxima fase prática pode ser:

```txt
Fase F.5 — Página pública simples / Landing beta
```

Ou:

```txt
Fase G — Polimento final e testes de regressão completa
```
