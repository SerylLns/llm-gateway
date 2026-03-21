import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.db import get_db


class LoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        elapsed_ms = int((time.time() - start) * 1000)

        if request.url.path in {"/health", "/docs", "/openapi.json", "/redoc"}:
            return response

        ip = request.client.host if request.client else "unknown"

        try:
            conn = get_db()
            conn.execute(
                """INSERT INTO request_logs (ip, route, status_code, response_time_ms)
                   VALUES (?, ?, ?, ?)""",
                (ip, request.url.path, response.status_code, elapsed_ms),
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

        return response
