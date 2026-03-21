import httpx

from app.config import settings
from app.providers.base import BaseProvider

BASE_URL = "https://api.mistral.ai/v1"


class MistralProvider(BaseProvider):
    def __init__(self):
        self._client = httpx.AsyncClient(timeout=30)

    async def complete(
        self, messages: list[dict], temperature: float = 0.3
    ) -> dict:
        payload = {
            "model": "mistral-small-latest",
            "messages": messages,
            "temperature": temperature,
        }

        resp = await self._client.post(
            f"{BASE_URL}/chat/completions",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.mistral_api_key}",
            },
        )
        resp.raise_for_status()
        body = resp.json()

        text = body["choices"][0]["message"]["content"].strip()
        usage = body.get("usage", {})

        return {
            "content": text,
            "tokens_in": usage.get("prompt_tokens", 0),
            "tokens_out": usage.get("completion_tokens", 0),
        }
