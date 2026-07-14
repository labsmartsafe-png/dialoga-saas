# Guia — Fase B: Áudio no WhatsApp

## Objetivo

Permitir que o dIAloga+ receba áudio no WhatsApp QR/Evolution, transcreva com Gemini e use a transcrição dentro do fluxo/CRM.

## Comportamento implementado

Quando o lead envia um áudio:

1. Webhook Evolution recebe `audioMessage`.
2. Backend chama Evolution:

```txt
POST /chat/getBase64FromMediaMessage/{instance}
```

3. O áudio é baixado em base64.
4. Gemini transcreve o áudio.
5. O texto transcrito entra no fluxo como mensagem do usuário.
6. O lead/contexto são atualizados normalmente.
7. A Inbox mostra a mensagem como:

```txt
🎧 Áudio transcrito: ...
```

## Arquivos alterados

```txt
backend/app/services/evolution_service.py
backend/app/services/ai_provider.py
backend/app/routers/whatsapp_evolution.py
```

## Funções novas

### `evolution_service.py`

```python
get_base64_from_media_message(instance_name, message_key, convert_to_mp4=True)
is_audio_message(message)
extract_audio_mimetype(message)
```

### `ai_provider.py`

```python
transcribe_audio_base64(audio_base64, mime_type="audio/mp4")
```

### `whatsapp_evolution.py`

Adicionado fluxo para:

```txt
audioMessage -> baixar mídia -> transcrever -> processar como texto
```

## Fallback

Se a transcrição falhar, o sistema não avança o fluxo para não preencher variáveis com erro.

Nesse caso, responde ao lead:

```txt
Recebi seu áudio, mas não consegui transcrever agora. Pode enviar sua mensagem em texto, por favor?
```

## Testes feitos no sandbox

```txt
python -m py_compile backend/app/services/ai_provider.py backend/app/services/evolution_service.py backend/app/routers/whatsapp_evolution.py
OK: áudio Evolution transcrito entra no fluxo e atualiza lead
```

## Como aplicar

Substitua estes arquivos:

```txt
backend/app/services/evolution_service.py
backend/app/services/ai_provider.py
backend/app/routers/whatsapp_evolution.py
```

Adicione este guia:

```txt
docs/GUIA_FASE_B_AUDIO_WHATSAPP.md
```

Valide:

```powershell
python -m py_compile backend/app/services/ai_provider.py backend/app/services/evolution_service.py backend/app/routers/whatsapp_evolution.py
```

Commit:

```powershell
git add backend/app/services/evolution_service.py backend/app/services/ai_provider.py backend/app/routers/whatsapp_evolution.py docs/GUIA_FASE_B_AUDIO_WHATSAPP.md
git commit -m "Adiciona transcricao de audio no WhatsApp"
git push
```

## Teste em produção

1. Aguardar deploy.
2. Enviar áudio para o número conectado via QR.
3. Se o fluxo estiver aguardando input, o áudio transcrito deve alimentar o campo.
4. Conferir na Inbox/Leads se aparece:

```txt
🎧 Áudio transcrito: ...
```

## Observações

- Esta primeira versão apenas transcreve áudio recebido.
- Ainda não responde com áudio.
- A transcrição usa Gemini, então consome cota/token.
- Se o lead estiver em atendimento humano ou a conexão estiver pausada, a mensagem transcrita é registrada, mas o bot continua respeitando a pausa.
