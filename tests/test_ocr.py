import asyncio
import json

import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.providers.gemini import GeminiProvider
from app.routes import ocr as ocr_route

GEMINI_REPLY = {
    "candidates": [{"content": {"parts": [{"text": "{\"item\": 2}"}]}}],
    "usageMetadata": {"promptTokenCount": 900, "candidatesTokenCount": 12},
}


def recording_provider():
    sent = []

    def handler(request):
        sent.append(json.loads(request.content))
        return httpx.Response(200, json=GEMINI_REPLY)

    provider = GeminiProvider()
    provider._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return provider, sent


def test_ocr_without_references_sends_the_image_then_the_prompt():
    provider, sent = recording_provider()

    result = asyncio.run(provider.ocr("UEhPVE8=", "image/jpeg", "Describe it"))

    assert sent[0]["contents"][0]["parts"] == [
        {"inline_data": {"mime_type": "image/jpeg", "data": "UEhPVE8="}},
        {"text": "Describe it"},
    ]
    assert "thinkingConfig" not in sent[0]["generationConfig"]
    assert result == {"content": "{\"item\": 2}", "tokens_in": 900, "tokens_out": 12}


def test_ocr_labels_each_reference_before_the_image_to_analyse():
    provider, sent = recording_provider()
    references = [
        {"label": "Item 1 · Bathroom", "image": "QkFUSA==", "mime_type": "image/jpeg"},
        {"label": "Item 2 · Bed", "image": "QkVE", "mime_type": "image/png"},
    ]

    asyncio.run(provider.ocr("UEhPVE8=", "image/jpeg", "Which item?", references=references))

    assert sent[0]["contents"][0]["parts"] == [
        {"text": "Item 1 · Bathroom"},
        {"inline_data": {"mime_type": "image/jpeg", "data": "QkFUSA=="}},
        {"text": "Item 2 · Bed"},
        {"inline_data": {"mime_type": "image/png", "data": "QkVE"}},
        {"inline_data": {"mime_type": "image/jpeg", "data": "UEhPVE8="}},
        {"text": "Which item?"},
    ]


def test_ocr_passes_the_thinking_budget():
    provider, sent = recording_provider()

    asyncio.run(provider.ocr("UEhPVE8=", "image/jpeg", "Which item?", thinking_budget=0))

    assert sent[0]["generationConfig"]["thinkingConfig"] == {"thinkingBudget": 0}


def test_ocr_route_forwards_references_and_thinking_budget(monkeypatch):
    calls = []

    async def fake_ocr(image, mime_type, prompt, references=(), thinking_budget=None):
        calls.append({"image": image, "mime_type": mime_type, "prompt": prompt,
                      "references": references, "thinking_budget": thinking_budget})
        return {"content": "{\"item\": 2}", "tokens_in": 900, "tokens_out": 12}

    monkeypatch.setattr(ocr_route.gemini, "ocr", fake_ocr)

    with TestClient(app) as client:
        response = client.post(
            "/v1/ocr",
            headers={"Authorization": "Bearer test-master-key"},
            json={"image": "UEhPVE8=", "mime_type": "image/jpeg", "prompt": "Which item?",
                  "references": [{"label": "Item 2 · Bed", "image": "QkVE"}], "thinking_budget": 0},
        )

    assert response.status_code == 200
    assert response.json()["text"] == "{\"item\": 2}"
    assert calls == [{"image": "UEhPVE8=", "mime_type": "image/jpeg", "prompt": "Which item?",
                      "references": [{"label": "Item 2 · Bed", "image": "QkVE", "mime_type": "image/jpeg"}],
                      "thinking_budget": 0}]


def test_ocr_route_still_accepts_the_single_image_body(monkeypatch):
    calls = []

    async def fake_ocr(image, mime_type, prompt, references=(), thinking_budget=None):
        calls.append((references, thinking_budget))
        return {"content": "text", "tokens_in": 1, "tokens_out": 1}

    monkeypatch.setattr(ocr_route.gemini, "ocr", fake_ocr)

    with TestClient(app) as client:
        response = client.post("/v1/ocr", headers={"Authorization": "Bearer test-master-key"},
                               json={"image": "UEhPVE8="})

    assert response.status_code == 200
    assert calls == [([], None)]
