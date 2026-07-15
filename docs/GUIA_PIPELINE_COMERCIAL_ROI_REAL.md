# Guia — Pipeline comercial simples + ROI real

## Objetivo

Evoluir o ROI do dIAloga+ de estimativa por agendamento para também considerar vendas/conversões reais marcadas manualmente no CRM.

## O que foi implementado

Agora um lead pode ser marcado como:

```txt
convertido
perdido
```

E, quando convertido, pode receber um valor real de venda:

```txt
deal_value
```

Quando perdido, pode receber um motivo:

```txt
lost_reason
```

## Campos novos em `leads`

```txt
deal_value FLOAT
converted_at TIMESTAMP
lost_reason TEXT
```

Adicionados via auto-migração aditiva em `backend/app/database.py`.

## Backend alterado

```txt
backend/app/models.py
backend/app/database.py
backend/app/schemas.py
backend/app/routers/leads.py
backend/app/routers/dashboard.py
```

### `LeadUpdate` agora aceita

```json
{
  "status": "convertido",
  "deal_value": 500
}
```

ou:

```json
{
  "status": "perdido",
  "lost_reason": "Cliente sem orçamento"
}
```

Quando `status = convertido`, o backend preenche automaticamente:

```txt
converted_at
```

se ainda estiver vazio.

## Dashboard atualizado

Novas métricas no `/api/dashboard/metrics`:

```txt
converted_count
lost_count
real_conversion_rate
actual_revenue
```

### Cálculos

```txt
actual_revenue = soma(deal_value dos leads convertidos)
```

```txt
real_conversion_rate = leads convertidos / leads reais
```

## Frontend alterado

```txt
frontend/leads.html
frontend/dashboard.html
```

### Na tela Leads

Ao mudar o status para:

```txt
Convertido
```

é solicitado o valor real da venda.

Ao mudar para:

```txt
Perdido
```

é solicitado o motivo da perda.

### No Dashboard

Novos cards:

```txt
Receita real convertida
Conversão real
```

## Testes feitos no sandbox

```txt
python -m py_compile backend/app/models.py backend/app/database.py backend/app/schemas.py backend/app/routers/leads.py backend/app/routers/dashboard.py
node --check frontend/js/api.js
node --check /tmp/leads_inline.js
node --check /tmp/dashboard_inline.js
OK: pipeline comercial e receita real funcionando
```

## Como aplicar

Substitua os arquivos:

```txt
backend/app/models.py
backend/app/database.py
backend/app/schemas.py
backend/app/routers/leads.py
backend/app/routers/dashboard.py
frontend/leads.html
frontend/dashboard.html
docs/GUIA_PIPELINE_COMERCIAL_ROI_REAL.md
```

Valide:

```powershell
python -m py_compile backend/app/models.py backend/app/database.py backend/app/schemas.py backend/app/routers/leads.py backend/app/routers/dashboard.py
node --check frontend/js/api.js
```

Commit:

```powershell
git add backend/app/models.py backend/app/database.py backend/app/schemas.py backend/app/routers/leads.py backend/app/routers/dashboard.py frontend/leads.html frontend/dashboard.html docs/GUIA_PIPELINE_COMERCIAL_ROI_REAL.md
git commit -m "Adiciona pipeline comercial e ROI real"
git push
```

## Teste em produção

1. Abrir `/leads.html`.
2. Alterar um lead real para `Convertido`.
3. Informar valor, por exemplo:

```txt
500
```

4. Abrir `/dashboard.html`.
5. Conferir:

```txt
Receita real convertida
Conversão real
```

6. Alterar outro lead para `Perdido` e informar motivo.
7. Conferir se o motivo aparece nos detalhes do lead.

## Próximo passo recomendado

Depois de validar, seguir para uma destas opções:

1. Dashboard por origem/tag/nicho;
2. Google Calendar;
3. Configuração de pipeline por nicho;
4. Painel Admin.
