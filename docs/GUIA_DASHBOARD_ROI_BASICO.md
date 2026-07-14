# Guia — Dashboard ROI básico

## Objetivo

Evoluir o Dashboard para começar a mostrar métricas comerciais/operacionais que ajudam a vender valor, não apenas volume.

## Arquivos criados/alterados

```txt
backend/app/routers/dashboard.py
frontend/dashboard.html
docs/GUIA_DASHBOARD_ROI_BASICO.md
```

## Métricas novas

Além das métricas antigas, o endpoint `/api/dashboard/metrics` agora retorna:

```txt
real_leads_count
simulator_leads_count
human_pending_count
human_active_count
appointments_total
appointments_requested
appointments_confirmed
appointments_done
appointments_today
appointments_next_7_days
real_leads_with_appointment
appointment_conversion_rate
```

## O que aparece no Dashboard

Novos cards:

```txt
Leads reais
Aguardando humano
Agend. hoje
Agend. confirmados
Conversão p/ agenda
```

O card `Conversão p/ agenda` calcula:

```txt
leads reais com pelo menos 1 agendamento / total de leads reais
```

## Compatibilidade

O endpoint continua retornando os campos antigos usados pelo dashboard:

```txt
flows_count
active_flows_count
leads_count
leads_today
leads_this_week
conversations_total
conversations_simulated
conversations_real
leads_by_day
recent_flows
recent_leads
```

## Testes feitos no sandbox

```txt
python -m py_compile backend/app/routers/dashboard.py backend/app/main.py
node --check frontend/js/api.js
node --check /tmp/dashboard_inline.js
OK: dashboard ROI básico calcula métricas
OK syntax clean
```

## Como aplicar

Substitua/crie:

```txt
backend/app/routers/dashboard.py
frontend/dashboard.html
docs/GUIA_DASHBOARD_ROI_BASICO.md
```

Valide:

```powershell
python -m py_compile backend/app/routers/dashboard.py backend/app/main.py
node --check frontend/js/api.js
```

Commit:

```powershell
git add backend/app/routers/dashboard.py frontend/dashboard.html docs/GUIA_DASHBOARD_ROI_BASICO.md
git commit -m "Adiciona dashboard ROI basico"
git push
```

## Teste em produção

1. Abrir `/dashboard.html`.
2. Conferir se os novos cards aparecem.
3. Criar um agendamento vinculado a lead real.
4. Atualizar o dashboard.
5. Conferir alteração em:

```txt
Agend. hoje
Agend. confirmados
Conversão p/ agenda
```

## Próximo passo recomendado

Depois desse dashboard básico:

1. Dashboard ROI financeiro com valor estimado por agendamento/conversão;
2. Configuração de ticket médio por nicho;
3. Relatórios por origem/campanha;
4. Google Calendar.
