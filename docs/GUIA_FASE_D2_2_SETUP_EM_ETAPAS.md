# Guia — Fase D.2.2: Setup guiado em etapas

## Objetivo

Evitar que o Setup faça tudo em uma única requisição pesada e cause timeout/estouro de memória no Render Free.

Agora o setup é executado em etapas:

```txt
1. Escolher nicho
2. Preencher dados do negócio
3. Criar fluxo
4. Criar base de conhecimento
5. Ensinar IA / indexar
6. Finalizar
```

## Por que foi feito

A versão anterior podia executar:

```txt
criar fluxo + criar base + indexar IA + salvar ROI
```

tudo de uma vez.

A indexação com Gemini pode ser pesada e causar:

```txt
Render Free: ran out of memory > 512MB
```

Com etapas separadas, se a IA falhar, o fluxo e a base já continuam criados.

## Arquivos alterados

```txt
backend/app/services/niche_setup_service.py
backend/app/routers/setup.py
frontend/js/api.js
frontend/setup.html
docs/GUIA_FASE_D2_2_SETUP_EM_ETAPAS.md
```

## Endpoints novos/ajustados

### Listar nichos

```txt
GET /api/setup/niches
```

### Criar fluxo

```txt
POST /api/setup/create-flow
```

Cria apenas o fluxo e salva ROI, sem criar/indexar IA.

### Criar base de conhecimento

```txt
POST /api/setup/create-kb
```

Cria a base e define como padrão em `AISettings`, mas não indexa.

### Indexar base

```txt
POST /api/setup/index-kb
```

Executa a etapa pesada de embeddings/Gemini isoladamente.

## Frontend

A tela:

```txt
frontend/setup.html
```

agora é um wizard simples com passos visuais.

## API JS

Adicionados:

```js
setupCreateFlow(body)
setupCreateKb(body)
setupIndexKb(body)
```

## Testes feitos

```txt
python -m py_compile backend/app/services/niche_setup_service.py backend/app/routers/setup.py backend/app/main.py
node --check frontend/js/api.js
node --check /tmp/setup_inline.js
OK setup html clean
OK: setup em etapas cria fluxo, base e indexa separadamente
```

## Como aplicar

Substitua:

```txt
backend/app/services/niche_setup_service.py
backend/app/routers/setup.py
frontend/js/api.js
frontend/setup.html
docs/GUIA_FASE_D2_2_SETUP_EM_ETAPAS.md
```

Valide:

```powershell
python -m py_compile backend/app/services/niche_setup_service.py backend/app/routers/setup.py backend/app/main.py
node --check frontend/js/api.js
```

Commit:

```powershell
git add backend/app/services/niche_setup_service.py backend/app/routers/setup.py frontend/js/api.js frontend/setup.html docs/GUIA_FASE_D2_2_SETUP_EM_ETAPAS.md
git commit -m "Transforma setup em etapas"
git push
```

## Teste em produção

1. Abrir `/setup.html`.
2. Escolher nicho.
3. Preencher dados.
4. Clicar `Criar fluxo`.
5. Clicar `Criar base de conhecimento`.
6. Clicar `Ensinar IA agora`.
7. Se indexação falhar, tentar novamente pela tela IA.

## Observação

Essa abordagem é mais parecida com onboarding de SaaS e reduz risco operacional.
