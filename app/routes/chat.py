import time
import logging

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.db import get_db
from app.providers.gemini import GeminiProvider
from app.providers.mistral import MistralProvider

logger = logging.getLogger(__name__)
router = APIRouter()

gemini = GeminiProvider()
mistral = MistralProvider()


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str = "default"
    messages: list[Message]
    temperature: float = 0.3


@router.post("/v1/chat/completions")
async def chat_completions(body: ChatRequest, request: Request):
    start = time.time()
    messages = [m.model_dump() for m in body.messages]
    provider_used = None
    result = None

    if body.model == "gemini":
        provider_used = "gemini"
        result = await gemini.complete(messages, body.temperature)
    elif body.model == "mistral":
        provider_used = "mistral"
        result = await mistral.complete(messages, body.temperature)
    else:
        # default: try gemini, fallback mistral
        try:
            provider_used = "gemini"
            result = await gemini.complete(messages, body.temperature)
        except Exception as e:
            logger.warning(f"Gemini failed, falling back to Mistral: {e}")
            provider_used = "mistral"
            result = await mistral.complete(messages, body.temperature)

    elapsed_ms = int((time.time() - start) * 1000)

    # update log with provider details
    try:
        ip = request.client.host if request.client else "unknown"
        conn = get_db()
        conn.execute(
            """UPDATE request_logs
               SET model_requested = ?, provider_used = ?, tokens_in = ?, tokens_out = ?
               WHERE ip = ? AND route = '/v1/chat/completions'
               ORDER BY id DESC LIMIT 1""",
            (body.model, provider_used, result["tokens_in"], result["tokens_out"], ip),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass

    return {
        "choices": [
            {"message": {"role": "assistant", "content": result["content"]}}
        ],
        "usage": {
            "prompt_tokens": result["tokens_in"],
            "completion_tokens": result["tokens_out"],
        },
        "provider": provider_used,
        "response_time_ms": elapsed_ms,
    }
