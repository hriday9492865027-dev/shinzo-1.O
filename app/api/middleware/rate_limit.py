"""
Rate limiting middleware using SlowAPI.

Limits: RATE_LIMIT_PER_MINUTE requests per client IP per minute.
Configurable via settings.rate_limit_per_minute.

SlowAPI wraps slowapi which is built on limits library.
Falls back gracefully if SlowAPI is not installed (no rate limiting in dev).

Usage: registered in app/api/main.py startup.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def get_limiter():
    """Returns a configured SlowAPI Limiter, or None if slowapi not installed."""
    try:
        from slowapi import Limiter
        from slowapi.util import get_remote_address

        from app.core.config import get_settings

        settings = get_settings()
        limiter = Limiter(
            key_func=get_remote_address,
            default_limits=[f"{settings.rate_limit_per_minute}/minute"],
        )
        logger.info("Rate limiter enabled: %d req/min", settings.rate_limit_per_minute)
        return limiter
    except ImportError:
        logger.warning("slowapi not installed — rate limiting disabled.")
        return None


def register_rate_limiter(app) -> None:
    """
    Attach the SlowAPI limiter to the FastAPI app.
    Call from app/api/main.py after app creation.
    """
    limiter = get_limiter()
    if limiter is None:
        return

    try:
        from slowapi import _rate_limit_exceeded_handler
        from slowapi.errors import RateLimitExceeded

        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
        logger.info("Rate limiter registered.")
    except Exception as exc:
        logger.error("Failed to register rate limiter: %s", exc)
