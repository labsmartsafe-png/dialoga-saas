# Guia — Dashboard ROI financeiro básico

## Objetivo

Adicionar estimativa financeira simples ao Dashboard, usando um ticket médio configurável.

## O que foi implementado

### Novo model

```txt
ROISettings
```

Tabela:

```txt
roi_settings
```

Campos:

```txt
id
owner_id
average_ticket
currency
created_at
updated_at
```

Como é tabela nova, `create_all()` cria automaticamente.

### Novos schemas

```txt
ROISettingsUpdate
ROISettingsOut
```

### Novos endpoints

```txt
GET /api/dashboard/roi-settings
PUT /api/dashboard/roi-settings
```

Body do PUT:

```json
{
  "average_ticket": 250,
  "currency": "BRL"
}
```

### Métricas novas no `/api/dashboard/metrics`

```txt
roi_average_ticket
roi_currency
estimated_confirmed_revenue
estimated_done_revenue
estimated_pipeline_revenue
```

## Cálculos

```txt
estimated_confirmed_revenue = agendamentos_confirmados * ticket_medio
estimated_done_revenue = agendamentos_realizados * ticket_medio
estimated_pipeline_revenue = (agendamentos_solicitados + agendamentos_confirmados) * ticket_medio
```

## Frontend

Na tela:

```txt
frontend/dashboard.html
```

Foi adicionado:

- card de configuração de ticket médio;
- card `Receita confirmada estim.`;
- card `Pipeline estimado`;
- hint com receita realizada estimada.

## Arquivos alterados

```txt
backend/app/models.py
backend/app/schemas.py
backend/app/routers/dashboard.py
frontend/js/api.js
frontend/dashboard.html
docs/GUIA_DASHBOARD_ROI_FINANCEIRO.md
```

## Testes feitos

```txt
python -m py_compile backend/app/models.py backend/app/schemas.py backend/app/routers/dashboard.py backend/app/main.py
node --check frontend/js/api.js
node --check /tmp/dashboard_inline.js
OK: ROI financeiro básico funcionando
```

## Como aplicar

Substitua:

```txt
backend/app/models.py
backend/app/schemas.py
backend/app/routers/dashboard.py
frontend/js/api.js
frontend/dashboard.html
docs/GUIA_DASHBOARD_ROI_FINANCEIRO.md
```

Valide:

```powershell
python -m py_compile backend/app/models.py backend/app/schemas.py backend/app/routers/dashboard.py backend/app/main.py
node --check frontend/js/api.js
```

Commit:

```powershell
git add backend/app/models.py backend/app/schemas.py backend/app/routers/dashboard.py frontend/js/api.js frontend/dashboard.html docs/GUIA_DASHBOARD_ROI_FINANCEIRO.md
git commit -m "Adiciona ROI financeiro basico no dashboard"
git push
```

## Teste em produção

1. Abrir `/dashboard.html`.
2. Informar ticket médio, por exemplo:

```txt
250
```

3. Criar/agendar um atendimento confirmado.
4. Atualizar Dashboard.
5. Conferir:

```txt
Receita confirmada estim.
Pipeline estimado
Conversão p/ agenda
```

## Observação

Este é ROI estimado. Não representa faturamento real até que exista integração de pagamento ou marcação manual de venda concluída.
