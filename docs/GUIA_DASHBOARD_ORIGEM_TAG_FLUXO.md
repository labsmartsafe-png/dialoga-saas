# Guia — Dashboard por origem, tag e fluxo

## Objetivo

Adicionar análises segmentadas ao Dashboard para entender quais canais, tags e fluxos geram mais resultado.

## Arquivos alterados

```txt
backend/app/routers/dashboard.py
frontend/dashboard.html
docs/GUIA_DASHBOARD_ORIGEM_TAG_FLUXO.md
```

## Métricas novas no `/api/dashboard/metrics`

### `leads_by_source`

Lista por origem:

```json
{
  "source": "whatsapp_evolution",
  "total": 10,
  "converted": 3,
  "conversion_rate": 30,
  "revenue": 1500
}
```

### `tags_summary`

Top 10 tags:

```json
{
  "tag": "urgente",
  "total": 5,
  "converted": 2,
  "conversion_rate": 40,
  "revenue": 1000
}
```

### `flows_performance`

Performance por fluxo:

```json
{
  "flow_id": 1,
  "flow_name": "Clínica - Avaliação",
  "leads": 20,
  "appointments": 6,
  "converted": 4,
  "conversion_rate": 20,
  "revenue": 2000
}
```

## Frontend

Na tela:

```txt
frontend/dashboard.html
```

Foram adicionados cards/tabelas:

```txt
Performance por origem
Top tags
Performance por fluxo
```

## Testes feitos

```txt
python -m py_compile backend/app/routers/dashboard.py backend/app/main.py
node --check frontend/js/api.js
node --check /tmp/dashboard_inline.js
OK: dashboard por origem/tag/fluxo funcionando
```

## Como aplicar

Substitua:

```txt
backend/app/routers/dashboard.py
frontend/dashboard.html
docs/GUIA_DASHBOARD_ORIGEM_TAG_FLUXO.md
```

Valide:

```powershell
python -m py_compile backend/app/routers/dashboard.py backend/app/main.py
node --check frontend/js/api.js
```

Commit:

```powershell
git add backend/app/routers/dashboard.py frontend/dashboard.html docs/GUIA_DASHBOARD_ORIGEM_TAG_FLUXO.md
git commit -m "Adiciona dashboard por origem tag e fluxo"
git push
```

## Teste em produção

1. Criar leads com origens diferentes.
2. Adicionar tags em alguns leads.
3. Marcar alguns como convertidos com valor real.
4. Abrir `/dashboard.html`.
5. Verificar:

```txt
Performance por origem
Top tags
Performance por fluxo
```

## Próximo passo recomendado

Depois disso, seguir para uma destas etapas:

1. Configuração de pipeline por nicho;
2. Google Calendar;
3. Painel Admin;
4. Relatórios exportáveis em PDF/CSV.
