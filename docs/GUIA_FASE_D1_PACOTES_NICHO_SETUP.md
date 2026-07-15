# Guia — Fase D.1: Pacotes de nicho + Setup inicial

## Objetivo

Transformar o dIAloga+ em um produto mais fácil de configurar e vender por nicho.

Em vez de o usuário começar do zero no Builder, ele escolhe um pacote pronto:

```txt
Clínica / Odonto
Petshop
Veículos
Suporte técnico
```

E o sistema cria um fluxo inicial com sugestões de pipeline, tags, tipos de agenda e base de conhecimento.

## O que foi implementado

### Backend

Novo serviço:

```txt
backend/app/services/niche_setup_service.py
```

Novo router:

```txt
backend/app/routers/setup.py
```

Endpoints:

```txt
GET /api/setup/niches
POST /api/setup/apply
```

### Frontend

Nova tela:

```txt
frontend/setup.html
```

Menu atualizado nos HTML principais para incluir:

```txt
Setup
```

## Pacotes disponíveis

### 1. Clínica / Odonto

Cria fluxo para:

```txt
recepção
procedimento de interesse
nome
telefone
preferência de horário
encaminhamento humano/agendamento
```

Pipeline sugerido:

```txt
clinica
```

Tipos de agenda:

```txt
avaliacao
consulta
```

Tags sugeridas:

```txt
avaliacao
procedimento
urgente
retorno
lead_quente
```

---

### 2. Petshop

Cria fluxo para:

```txt
serviço
nome do pet
porte
preferência de horário
encaminhamento humano/agendamento
```

Pipeline sugerido:

```txt
petshop
```

Tipos de agenda:

```txt
banho_tosa
retorno
```

Tags sugeridas:

```txt
banho_tosa
vacina
retorno
cliente_recorrente
urgente
```

---

### 3. Veículos

Cria fluxo para:

```txt
modelo de interesse
forma de compra
veículo na troca
prazo de compra
encaminhamento para consultor
```

Pipeline sugerido:

```txt
veiculos
```

Tipos de agenda:

```txt
visita
test_drive
```

Tags sugeridas:

```txt
test_drive
financiamento
troca
lead_quente
proposta
```

---

### 4. Suporte técnico

Cria fluxo para:

```txt
recepção
pergunta se já falou com suporte operacional
número do chamado
local
dúvida
encaminhamento humano
```

Pipeline sugerido:

```txt
suporte_tecnico
```

Tipo de agenda:

```txt
suporte
```

Tags sugeridas:

```txt
chamado
urgente
campo
aguardando_humano
suporte_n2
```

## O que o setup cria automaticamente

Ao clicar em `Usar este pacote`, o sistema cria:

```txt
um novo Flow guiado
```

E retorna:

```txt
flow_id
flow_name
pipeline_type
appointment_types
suggested_tags
knowledge_base_seed
next_steps
```

## O que ainda NÃO faz automaticamente

Por segurança, esta primeira versão ainda não:

- indexa base de conhecimento automaticamente;
- conecta WhatsApp automaticamente;
- altera configurações existentes;
- cria agenda automática;
- aplica tags automaticamente em leads antigos.

O usuário recebe o texto de base sugerido e deve revisar/copiar para a tela IA.

## Arquivos criados

```txt
backend/app/services/niche_setup_service.py
backend/app/routers/setup.py
frontend/setup.html
docs/GUIA_FASE_D1_PACOTES_NICHO_SETUP.md
```

## Arquivos alterados

```txt
backend/app/main.py
frontend/js/api.js
frontend/dashboard.html
frontend/builder.html
frontend/leads.html
frontend/inbox.html
frontend/agenda.html
frontend/ia.html
frontend/configuracoes.html
```

## Métodos adicionados no `frontend/js/api.js`

```js
listNichePackages()
applyNichePackage(body)
```

## Testes feitos no sandbox

```txt
python -m py_compile backend/app/services/niche_setup_service.py backend/app/routers/setup.py backend/app/main.py backend/app/routers/flows.py
node --check frontend/js/api.js
node --check /tmp/setup_inline.js
OK html clean/menu setup
OK: pacotes de nicho listam e criam fluxos no sandbox
```

## Como aplicar

Substitua/crie:

```txt
backend/app/services/niche_setup_service.py
backend/app/routers/setup.py
backend/app/main.py
frontend/js/api.js
frontend/setup.html
frontend/dashboard.html
frontend/builder.html
frontend/leads.html
frontend/inbox.html
frontend/agenda.html
frontend/ia.html
frontend/configuracoes.html
docs/GUIA_FASE_D1_PACOTES_NICHO_SETUP.md
```

Valide:

```powershell
python -m py_compile backend/app/services/niche_setup_service.py backend/app/routers/setup.py backend/app/main.py
node --check frontend/js/api.js
```

Commit:

```powershell
git add backend/app/services/niche_setup_service.py backend/app/routers/setup.py backend/app/main.py frontend/js/api.js frontend/setup.html frontend/dashboard.html frontend/builder.html frontend/leads.html frontend/inbox.html frontend/agenda.html frontend/ia.html frontend/configuracoes.html docs/GUIA_FASE_D1_PACOTES_NICHO_SETUP.md
git commit -m "Adiciona setup por nicho com pacotes prontos"
git push
```

## Teste em produção

1. Abrir:

```txt
/setup.html
```

2. Informar nome do negócio, opcional.
3. Escolher pacote, por exemplo:

```txt
Clínica / Odonto
```

4. Clicar:

```txt
Usar este pacote
```

5. Confirmar que um fluxo novo foi criado.
6. Clicar em:

```txt
Abrir fluxo
```

7. Revisar no Builder.
8. Copiar o texto sugerido para a tela IA.
9. Conectar esse fluxo em Configurações > WhatsApp.

## Próximo passo recomendado

Depois de validar esta fase, seguir para:

```txt
Fase D.2 — Setup guiado completo
```

A D.2 deve perguntar dados do negócio e preencher automaticamente:

- nome da empresa;
- endereço;
- horários;
- serviços;
- contatos;
- ticket médio;
- texto base de conhecimento personalizado;
- fluxo com variáveis adaptadas.
