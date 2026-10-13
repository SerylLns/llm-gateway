import itertools

import httpx

from app.config import settings
from app.providers.base import BaseProvider

BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


class GeminiProvider(BaseProvider):
    def __init__(self):
        self._keys = itertools.cycle(settings.gemini_keys_list)
        self._client = httpx.AsyncClient(timeout=30)

    def _next_key(self) -> str:
        return next(self._keys)

    async def complete(
        self, messages: list[dict], temperature: float = 0.3
    ) -> dict:
        contents = []
        for m in messages:
            role = "model" if m["role"] == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": m["content"]}]})

        payload = {
            "contents": contents,
            "generationConfig": {"temperature": temperature},
        }

        key = self._next_key()
        url = f"{BASE_URL}/models/{settings.default_model}:generateContent"

        resp = await self._client.post(
            url,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": key,
            },
        )
        resp.raise_for_status()
        body = resp.json()

        text = body["candidates"][0]["content"]["parts"][0]["text"].strip()
        usage = body.get("usageMetadata", {})

        return {
            "content": text,
            "tokens_in": usage.get("promptTokenCount", 0),
            "tokens_out": usage.get("candidatesTokenCount", 0),
        }

    async def ocr(
        self,
        image_base64: str,
        mime_type: str = "image/png",
        prompt: str = "Extract all text from this image.",
        references: list[dict] = (),
        thinking_budget: int | None = None,
    ) -> dict:
        parts = []
        for reference in references:
            parts.append({"text": reference["label"]})
            parts.append({"inline_data": {"mime_type": reference["mime_type"], "data": reference["image"]}})
        parts.append({"inline_data": {"mime_type": mime_type, "data": image_base64}})
        parts.append({"text": prompt})

        generation_config = {"temperature": 0.1}
        if thinking_budget is not None:
            generation_config["thinkingConfig"] = {"thinkingBudget": thinking_budget}

        payload = {
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": generation_config,
        }

        key = self._next_key()
        url = f"{BASE_URL}/models/{settings.default_model}:generateContent"

        resp = await self._client.post(
            url,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": key,
            },
        )
        resp.raise_for_status()
        body = resp.json()

        text = body["candidates"][0]["content"]["parts"][0]["text"].strip()
        usage = body.get("usageMetadata", {})

        return {
            "content": text,
            "tokens_in": usage.get("promptTokenCount", 0),
            "tokens_out": usage.get("candidatesTokenCount", 0),
        }
