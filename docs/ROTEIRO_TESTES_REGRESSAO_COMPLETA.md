# Roteiro de Testes de Regressão Completa — dIAloga+ 2.0

> Objetivo: validar que as principais áreas do SaaS continuam funcionando depois das muitas evoluções implementadas: WhatsApp, IA, CRM, Inbox, Agenda, Google Calendar, Billing, Admin, Setup e Dashboard.

---

## 1. Preparação antes dos testes

### 1.1 Confirmar Git limpo

```powershell
git status
```

Esperado:

```txt
nothing to commit, working tree clean
```

Se houver alterações, commit antes dos testes.

---

### 1.2 Validar sintaxe local

Rode:

```powershell
python -m py_compile backend/app/models.py backend/app/database.py backend/app/schemas.py backend/app/main.py
python -m py_compile backend/app/routers/admin.py backend/app/routers/ai.py backend/app/routers/appointments.py backend/app/routers/billing.py backend/app/routers/calendar.py backend/app/routers/flows.py backend/app/routers/inbox.py backend/app/routers/leads.py backend/app/routers/setup.py backend/app/routers/whatsapp_connections.py backend/app/routers/whatsapp_evolution.py backend/app/routers/whatsapp_meta.py
python -m py_compile backend/app/services/ai_provider.py backend/app/services/billing_service.py backend/app/services/evolution_service.py backend/app/services/flow_engine.py backend/app/services/google_calendar_service.py backend/app/services/lead_service.py backend/app/services/niche_setup_service.py backend/app/services/plan_limits.py backend/app/services/rag_service.py backend/app/services/whatsapp_meta_service.py
node --check frontend/js/api.js
node --check frontend/js/auth.js
node --check frontend/js/config.js
node --check frontend/js/builder.js
node --check frontend/js/canvas.js
```

Esperado: não retornar erro.

---

### 1.3 Verificar scripts externos indesejados

Rode:

```powershell
Select-String -Path frontend/*.html -Pattern "kaspersky","cloudflareinsights","cdn-cgi","challenge-platform"
```

Esperado: não aparecer nada.

---

## 2. Testes de Login e sessão

### 2.1 Login

1. Acessar:

```txt
/login.html
```

2. Fazer login com usuário existente.

Esperado:

- redireciona para Dashboard;
- token salvo em `localStorage["whatsflow_token"]`;
- usuário aparece no topo.

---

### 2.2 Logout

1. Clicar em `Sair`.

Esperado:

- limpa sessão;
- volta para login.

---

## 3. Testes de navegação e UX

Acessar todas as telas principais:

```txt
/dashboard.html
/setup.html
/builder.html
/leads.html
/inbox.html
/agenda.html
/ia.html
/planos.html
/configuracoes.html
/admin.html
```

Esperado:

- todas carregam sem erro visual crítico;
- menu funciona;
- dark mode não deixa áreas brancas fora do padrão;
- Admin aparece apenas para admin.

---

## 4. Testes do Setup por nicho

### 4.1 Listar pacotes

1. Abrir:

```txt
/setup.html
```

2. Verificar pacotes:

```txt
Clínica / Odonto
Petshop
Veículos
Suporte técnico
```

Esperado: todos aparecem.

---

### 4.2 Setup em etapas

1. Escolher um nicho.
2. Preencher dados do negócio.
3. Criar fluxo.
4. Criar base.
5. Editar texto da base no textarea.
6. Ensinar IA agora ou pular.

Esperado:

- fluxo criado;
- base criada;
- se indexar, IA aprende;
- se falhar indexação, fluxo/base não são perdidos.

---

## 5. Testes de Fluxos / Builder

### 5.1 Abrir fluxo criado pelo Setup

1. Ir para `/builder.html`.
2. Abrir fluxo criado.
3. Verificar nós e conexões.

Esperado:

- fluxo aparece;
- nós não somem;
- salvar funciona.

---

### 5.2 Simulador

1. Iniciar simulação.
2. Responder perguntas.
3. Chegar em `+HUMANO` ou `+FIM`.

Esperado:

- fluxo segue corretamente;
- variáveis aparecem no contexto;
- não entra em loop.

---

## 6. Testes IA/RAG

### 6.1 Criar base manual

1. Ir para `/ia.html`.
2. Criar base.
3. Adicionar texto.
4. Clicar `Ensinar a IA`.

Esperado:

- chunks criados;
- conteúdo aparece em “O que esta IA já aprendeu”.

---

### 6.2 Perguntar para IA

1. Selecionar base.
2. Fazer pergunta que está no conteúdo.

Esperado:

- IA responde com base no conteúdo.

---

## 7. Testes WhatsApp QR / Evolution

### 7.1 Conexão QR

1. Ir para `/configuracoes.html`.
2. Criar conexão via QR.
3. Escanear QR.

Esperado:

- status conectado;
- número aparece na lista.

---

### 7.2 Mensagem real

1. Enviar mensagem de outro WhatsApp.
2. Bot responde.

Esperado:

- fluxo inicia;
- respostas chegam no WhatsApp.

---

### 7.3 `+PERG`

Responder:

```txt
1
```

ou:

```txt
Sim
```

Esperado: segue opção correta.

---

### 7.4 Áudio

1. Quando o bot pedir input, enviar áudio.

Esperado:

- áudio é transcrito;
- texto aparece como `🎧 Áudio transcrito:`;
- fluxo usa a transcrição.

---

## 8. Testes CRM / Leads

### 8.1 Lead real

Após mensagem WhatsApp:

1. Ir para `/leads.html`.

Esperado:

- lead aparece como `WhatsApp QR`;
- telefone preenchido;
- contexto atualizado.

---

### 8.2 Tags e notas

1. Abrir atendimento na Inbox.
2. Adicionar tag.
3. Adicionar nota interna.
4. Atualizar página.

Esperado:

- tag permanece;
- nota permanece;
- nota não vai para WhatsApp.

---

### 8.3 Excluir lead

1. Excluir lead em `/leads.html`.

Esperado:

- lead excluído;
- conversa preservada sem erro de chave estrangeira.

---

## 9. Testes de pausa do bot

### 9.1 Handoff automático

1. Fluxo chega em `+HUMANO`.
2. Lead manda nova mensagem.

Esperado:

- bot não responde;
- mensagem aparece no histórico/Inbox.

---

### 9.2 Humano assume pelo WhatsApp

1. Enquanto bot está no meio do fluxo, humano responde manualmente pelo WhatsApp conectado.
2. Lead responde.

Esperado:

- bot pausa automaticamente;
- lead fica `em_atendimento_humano`;
- bot não reinicia.

---

### 9.3 Pausa global

1. Em `/configuracoes.html`, clicar `Pausar automação`.
2. Lead novo manda mensagem.

Esperado:

- bot não responde;
- lead aparece no CRM como atendimento humano.

---

## 10. Testes Inbox Humano

1. Abrir `/inbox.html`.
2. Selecionar atendimento.
3. Clicar `Assumir`.
4. Enviar mensagem pelo painel.
5. Encerrar atendimento.

Esperado:

- mensagem chega no WhatsApp;
- status muda corretamente;
- atendimento encerrado some da Inbox.

---

## 11. Testes Agenda

### 11.1 Criar agendamento

1. Abrir `/agenda.html`.
2. Criar agendamento com lead.
3. Definir tipo e status.

Esperado:

- agendamento salvo;
- lead atualiza pipeline.

---

### 11.2 Inbox → Agenda

1. Abrir atendimento na Inbox.
2. Clicar `Agendar`.

Esperado:

- abre Agenda com lead pré-selecionado.

---

## 12. Testes Google Calendar

### 12.1 Conectar

1. Ir para `/configuracoes.html`.
2. Clicar `Conectar Google Calendar`.

Esperado:

- Google autoriza;
- volta com `calendar=connected`;
- status conectado aparece.

---

### 12.2 Sync

1. Criar agendamento confirmado.
2. Ver no Google Calendar.
3. Alterar horário.
4. Cancelar.

Esperado:

- cria evento;
- atualiza evento;
- remove/cancela evento.

---

## 13. Testes Dashboard

Abrir:

```txt
/dashboard.html
```

Validar:

- métricas carregam;
- ROI estimado aparece;
- ROI real aparece;
- próximos agendamentos aparecem;
- performance por origem/tag/fluxo aparece;
- pipeline por nicho aparece.

---

## 14. Testes Planos e limites

### 14.1 Tela Planos

Abrir:

```txt
/planos.html
```

Esperado:

- plano atual destacado;
- limites exibidos.

---

### 14.2 Limites

Testar em usuário Essencial:

- criar mais de 3 fluxos;
- criar mais de 1 conexão WhatsApp;
- criar mais de 3 bases IA.

Esperado:

- backend bloqueia com erro de limite.

---

## 15. Testes Admin

### 15.1 Acesso admin

1. Configurar `ADMIN_EMAILS`.
2. Logar com e-mail admin.
3. Abrir `/admin.html`.

Esperado:

- abre painel.

---

### 15.2 Não admin

Logar com usuário comum.

Esperado:

- link Admin oculto;
- acesso direto a `/admin.html` retorna 403.

---

### 15.3 Ações admin

Testar:

- alterar plano;
- ativar/desativar usuário;
- tornar/remover admin;
- ver compras pendentes;
- ver assinaturas;
- ver eventos de billing;
- ver saúde do sistema.

---

## 16. Testes Billing Hotmart/Eduzz

### 16.1 Usuário já existe

Enviar webhook aprovado com email existente.

Esperado:

- usuário ativado;
- plano aplicado;
- assinatura criada;
- evento registrado.

---

### 16.2 Usuário não existe

Enviar webhook aprovado com email inexistente.

Esperado:

- compra pendente criada;
- aparece no Admin.

Depois cadastrar usuário com mesmo email.

Esperado:

- pendência vira claimed;
- plano aplicado.

---

## 17. Testes de Go-live checklist

No Admin:

```txt
Saúde do sistema / Go-live
```

Verificar status de:

- SECRET_KEY;
- DATABASE_URL;
- CORS;
- WA_FERNET_KEYS;
- Evolution;
- Gemini;
- Google Calendar;
- Billing;
- Meta;
- ADMIN_EMAILS;
- domínio próprio;
- Render;
- e-mail oficial;
- termos e privacidade.

---

## 18. Checklist final de regressão

```txt
[ ] Login/logout
[ ] Setup em etapas
[ ] Builder/simulador
[ ] IA/RAG
[ ] WhatsApp QR
[ ] Áudio transcrito
[ ] Leads CRM
[ ] Pausas do bot
[ ] Inbox humano
[ ] Agenda interna
[ ] Google Calendar
[ ] Dashboard ROI
[ ] Planos e limites
[ ] Admin
[ ] Billing
[ ] Termos/Privacidade
[ ] Dark mode
[ ] Menus/navegação
```

---

## 19. Próxima recomendação após regressão

Se tudo passar, seguir para uma destas etapas:

1. Polimento UX global com sidebar/app shell moderno;
2. Domínio próprio e e-mails oficiais;
3. Testes beta fechados com 1-3 usuários reais;
4. Integração de e-mail transacional;
5. Verificação Google/Meta para produção.
