from fastapi import FastAPI

from app.db import init_db
from app.middleware.auth import AuthMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.logger import LoggerMiddleware
from app.routes import health, chat, ocr

app = FastAPI(title="LLM Gateway", version="1.0.0")

# Middleware (order matters: first added = outermost)
app.add_middleware(LoggerMiddleware)
app.add_middleware(AuthMiddleware)
app.add_middleware(RateLimitMiddleware)

# Routes
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(ocr.router)


@app.on_event("startup")
async def startup():
    init_db()
