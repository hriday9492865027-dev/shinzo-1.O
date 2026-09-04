"""
API Key validation middleware.

Validates the X-API-Key header on all routes except /health.
API keys are stored as Argon2 hashes in an environment variable or config.

For MVP: a single API key read from settings (API_KEY env var).
For production: extend to a DB-backed key registry with per-key rate limits.

Set in .env:
    API_KEY=your-secret-key-here
    API_AUTH_ENABLED=true    # set false to disable auth (dev/test mode)
"""
from __future__ import annotations

import logging
import os

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Routes that skip auth
_PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}

# Read from env at import time — secrets never in config objects
_API_KEY = os.environ.get("API_KEY", "")
_AUTH_ENABLED = os.environ.get("API_AUTH_ENABLED", "false").lower() == "true"


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    Simple API key header validation.
    Header: X-API-Key: <key>
    """

    async def dispatch(self, request: Request, call_next):
        if not _AUTH_ENABLED:
            return await call_next(request)

        if request.url.path in _PUBLIC_PATHS:
            return await call_next(request)

        api_key = request.headers.get("X-API-Key", "")
        if not api_key or not _validate_key(api_key):
            logger.warning("Rejected request with invalid API key from %s", request.client)
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API key."},
            )

        return await call_next(request)


def _validate_key(provided_key: str) -> bool:
    """
    Validate the provided key against the stored key.
    MVP: constant-time string comparison against plaintext env key.
    Production upgrade: use argon2-cffi to verify against a stored hash.
    """
    if not _API_KEY:
        # No key configured — reject everything when auth is enabled
        return False
    import hmac
    return hmac.compare_digest(provided_key.encode(), _API_KEY.encode())
