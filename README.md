# LLM Gateway

Proxy API centralisé pour LLM — Gemini (round-robin multi-clés) avec fallback Mistral.

## Setup

```bash
cp .env.example .env
# editer .env avec tes clés
docker compose up --build
```

## Env vars

| Variable | Description |
|----------|-------------|
| `MASTER_KEY` | Bearer token pour auth |
| `GEMINI_API_KEYS` | Clés Gemini séparées par virgule |
| `MISTRAL_API_KEY` | Clé Mistral (fallback) |
| `RATE_LIMIT_PER_MINUTE` | Limite par IP (défaut: 60) |

## Routes

### `GET /health`

```bash
curl https://llm.seryl.dev/health
```

### `POST /v1/chat/completions`

Format compatible OpenAI. `model` : `default` (Gemini → fallback Mistral), `gemini`, ou `mistral`.

```bash
curl https://llm.seryl.dev/v1/chat/completions \
  -H "Authorization: Bearer $MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"default","messages":[{"role":"user","content":"Hello"}]}'
```

Réponse :
```json
{
  "choices": [{"message": {"role": "assistant", "content": "Hello!"}}],
  "usage": {"prompt_tokens": 3, "completion_tokens": 2},
  "provider": "gemini",
  "response_time_ms": 620
}
```

### `POST /v1/ocr`

Image (base64) → texte via Gemini Vision.

```bash
echo "{\"image\":\"$(base64 -w 0 image.png)\",\"mime_type\":\"image/png\"}" > /tmp/ocr.json

curl https://llm.seryl.dev/v1/ocr \
  -H "Authorization: Bearer $MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d @/tmp/ocr.json
```

Réponse :
```json
{
  "text": "Texte extrait de l'image...",
  "usage": {"prompt_tokens": 266, "completion_tokens": 342},
  "response_time_ms": 3855
}
```

## Features

- Round-robin multi-clés Gemini
- Fallback automatique Gemini → Mistral
- Rate limiting par IP
- Logging SQLite (IP, route, provider, tokens, temps)
- Auth par Bearer token
