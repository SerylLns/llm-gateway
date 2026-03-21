import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _clean_old(self, ip: str):
        cutoff = time.time() - 60
        self._requests[ip] = [t for t in self._requests[ip] if t > cutoff]

    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/health":
            return await call_next(request)

        ip = request.client.host if request.client else "unknown"
        self._clean_old(ip)

        if len(self._requests[ip]) >= settings.rate_limit_per_minute:
            return JSONResponse(
                {"error": "rate limit exceeded", "retry_after_seconds": 60},
                status_code=429,
            )

        self._requests[ip].append(time.time())
        return await call_next(request)
