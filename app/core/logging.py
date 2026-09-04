"""
Structured logging setup.
Deliberately never logs raw user message content (per SAFETY_POLICY.md / API key & security
requirements in the roadmap) — only event metadata (route, status, latency, risk tier, ids).
"""
import logging
import sys

from app.core.config import get_settings


def configure_logging() -> None:
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        stream=sys.stdout,
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
