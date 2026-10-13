import time
import logging

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.db import get_db
from app.providers.gemini import GeminiProvider

logger = logging.getLogger(__name__)
router = APIRouter()

gemini = GeminiProvider()


class Reference(BaseModel):
    label: str
    image: str  # base64 encoded
    mime_type: str = "image/jpeg"


class OcrRequest(BaseModel):
    image: str  # base64 encoded
    mime_type: str = "image/png"
    prompt: str = "Extract all text from this image."
    references: list[Reference] = []
    thinking_budget: int | None = None


@router.post("/v1/ocr")
async def ocr(body: OcrRequest, request: Request):
    start = time.time()

    result = await gemini.ocr(
        body.image,
        body.mime_type,
        body.prompt,
        references=[reference.model_dump() for reference in body.references],
        thinking_budget=body.thinking_budget,
    )

    elapsed_ms = int((time.time() - start) * 1000)

    try:
        ip = request.client.host if request.client else "unknown"
        conn = get_db()
        conn.execute(
            """UPDATE request_logs
               SET model_requested = 'ocr', provider_used = 'gemini',
                   tokens_in = ?, tokens_out = ?
               WHERE ip = ? AND route = '/v1/ocr'
               ORDER BY id DESC LIMIT 1""",
            (result["tokens_in"], result["tokens_out"], ip),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass

    return {
        "text": result["content"],
        "usage": {
            "prompt_tokens": result["tokens_in"],
            "completion_tokens": result["tokens_out"],
        },
        "response_time_ms": elapsed_ms,
    }
