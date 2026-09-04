"""
FastAPI application instance. Mounts all routers and runs startup configuration.
Run locally with: uvicorn app.api.main:app --reload
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.middleware.auth import APIKeyMiddleware
from app.api.middleware.rate_limit import register_rate_limiter
from app.api.routes import chat, health, messages, proactive
from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Shinzo AI starting up")

    # Initialize database (creates tables if not exist)
    try:
        from app.memory.db import init_db
        init_db()
        logger.info("Database initialized.")
    except Exception as exc:
        logger.error("Database init failed: %s", exc)

    # Start proactive scheduler
    try:
        from app.proactive.scheduler import start_scheduler
        start_scheduler()
    except Exception as exc:
        logger.error("Proactive scheduler failed to start: %s", exc)

    yield

    # Graceful shutdown
    try:
        from app.proactive.scheduler import stop_scheduler
        stop_scheduler()
    except Exception:
        pass

    logger.info("Shinzo AI shutting down")


app = FastAPI(
    title="Shinzo AI",
    version="0.2.0",
    description="Emotionally intelligent AI companion — API",
    lifespan=lifespan,
)

# Middleware
app.add_middleware(APIKeyMiddleware)
register_rate_limiter(app)

# Routes
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(proactive.router)
app.include_router(messages.router)

