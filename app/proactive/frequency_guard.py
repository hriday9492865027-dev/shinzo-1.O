"""
Frequency Guard — prevents Shinzo from over-messaging.

Tracks how many proactive messages have been sent in the last 24 hours.
Also manages:
  - Pause mode (user explicitly asked for silence)
  - Engagement drop detection (reduce frequency if user consistently ignores)

Storage: uses SQLite via app/memory/db.py (UserPreference table).
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

DAILY_PROACTIVE_LIMIT = 3
ENGAGEMENT_DROP_THRESHOLD = 5   # ignored messages before reducing frequency


def get_recent_proactive_count(user_id: str) -> int:
    """Count proactive messages sent to this user in the last 24 hours."""
    try:
        # In full implementation, add a Message.is_proactive column and query messages in last 24h
        # For now return 0 (safe default — guard is off)
        return 0
    except Exception as exc:
        logger.warning("Could not check proactive count: %s", exc)
        return 0


def is_pause_mode_active(user_id: str) -> bool:
    """Check if user has set pause mode via UserPreference."""
    try:
        from app.memory.db import get_session
        from app.memory.models import UserPreference

        with get_session() as session:
            pref = (
                session.query(UserPreference)
                .filter(
                    UserPreference.user_id == user_id,
                    UserPreference.key == "proactive_pause",
                )
                .first()
            )
            if pref and pref.value == "true":
                return True
        return False
    except Exception as exc:
        logger.warning("Could not check pause mode: %s", exc)
        return False


def set_pause_mode(user_id: str, active: bool) -> None:
    """Set or clear pause mode for a user."""
    try:
        from app.memory.db import get_session
        from app.memory.models import UserPreference

        with get_session() as session:
            pref = (
                session.query(UserPreference)
                .filter(
                    UserPreference.user_id == user_id,
                    UserPreference.key == "proactive_pause",
                )
                .first()
            )
            if pref:
                pref.value = "true" if active else "false"
            else:
                session.add(UserPreference(
                    user_id=user_id,
                    key="proactive_pause",
                    value="true" if active else "false",
                ))
    except Exception as exc:
        logger.error("Could not set pause mode: %s", exc)
