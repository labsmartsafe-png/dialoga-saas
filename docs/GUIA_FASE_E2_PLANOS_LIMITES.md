# Guia — Fase E.2: Planos e limites

## Objetivo

Adicionar limites por plano para proteger margem e preparar o dIAloga+ para billing/Hotmart/Eduzz.

## Planos suportados

Planos legados e novos:

```txt
basico
essencial
profissional
performance
enterprise
admin
```

## Limites atuais

| Plano | Fluxos | Conexões WhatsApp | Bases IA | Limite IA/mês |
|---|---:|---:|---:|---:|
| basico | 3 | 1 | 3 | 500 |
| essencial | 3 | 1 | 3 | 500 |
| profissional | 10 | 2 | 10 | 2000 |
| performance | 50 | 5 | 50 | 10000 |
| enterprise | ilimitado | ilimitado | ilimitado | 50000 |
| admin | ilimitado | ilimitado | ilimitado | 100000 |

## Arquivo novo

```txt
backend/app/services/plan_limits.py
```

Responsável por:

```txt
normalizar plano
buscar limites
bloquear criação acima do limite
sincronizar limite mensal de IA
expor tabela pública de planos
```

## Arquivos alterados

```txt
backend/app/routers/flows.py
backend/app/routers/ai.py
backend/app/routers/whatsapp_connections.py
backend/app/routers/admin.py
backend/app/services/niche_setup_service.py
frontend/js/api.js
```

## Onde os limites são aplicados

### Fluxos

Em:

```txt
POST /api/flows
```

Bloqueia se exceder limite de fluxos.

### Conexões WhatsApp

Em:

```txt
POST /api/whatsapp/connections
POST /api/whatsapp/connections/evolution
```

Bloqueia se exceder limite de conexões.

### Bases de conhecimento

Em:

```txt
POST /api/ai/knowledge-bases
POST /api/setup/create-kb
```

Bloqueia se exceder limite de bases IA.

### Setup por nicho

Em:

```txt
POST /api/setup/create-flow
POST /api/setup/create-kb
```

Também respeita os limites do plano.

## Admin

Em:

```txt
PUT /api/admin/users/{user_id}
```

Quando o plano é alterado, o limite mensal de IA (`AISettings.monthly_ai_limit`) é sincronizado automaticamente.

Novo endpoint:

```txt
GET /api/admin/plans
```

Retorna a tabela de limites.

## API JS

Adicionado:

```js
adminPlans()
```

## Testes feitos no sandbox

```txt
python -m py_compile backend/app/services/plan_limits.py backend/app/routers/flows.py backend/app/routers/ai.py backend/app/routers/whatsapp_connections.py backend/app/routers/admin.py backend/app/services/niche_setup_service.py
node --check frontend/js/api.js
OK: limites por plano e sync AI funcionando
```

## Como aplicar

Substitua/crie:

```txt
backend/app/services/plan_limits.py
backend/app/routers/flows.py
backend/app/routers/ai.py
backend/app/routers/whatsapp_connections.py
backend/app/routers/admin.py
backend/app/services/niche_setup_service.py
frontend/js/api.js
docs/GUIA_FASE_E2_PLANOS_LIMITES.md
```

Valide:

```powershell
python -m py_compile backend/app/services/plan_limits.py backend/app/routers/flows.py backend/app/routers/ai.py backend/app/routers/whatsapp_connections.py backend/app/routers/admin.py backend/app/services/niche_setup_service.py
node --check frontend/js/api.js
```

Commit:

```powershell
git add backend/app/services/plan_limits.py backend/app/routers/flows.py backend/app/routers/ai.py backend/app/routers/whatsapp_connections.py backend/app/routers/admin.py backend/app/services/niche_setup_service.py frontend/js/api.js docs/GUIA_FASE_E2_PLANOS_LIMITES.md
git commit -m "Adiciona limites por plano"
git push
```

## Observação importante

O cadastro atual ainda pode criar usuário com plano `basico`. Isso é aceito como alias de `essencial`.

Em fase futura, se desejar, alterar o cadastro para criar diretamente:

```txt
plan = "essencial"
```

## Próximo passo recomendado

Depois de validar os limites:

1. Ocultar link Admin para não-admin no frontend;
2. Criar tela/estrutura de planos no Admin;
3. Integrar Hotmart/Eduzz para ativar plano automaticamente;
4. Implementar bloqueios/avisos visuais antes de chegar no limite.
