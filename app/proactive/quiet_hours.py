"""
Quiet Hours — user-defined do-not-disturb windows.

Reads quiet_hours_start and quiet_hours_end from settings (HH:MM format).
If current local time falls within the window, proactive messages are blocked.

Cross-midnight windows are supported (e.g., 22:00–08:00).
"""
from __future__ import annotations

from datetime import datetime, time


def _parse_time(t: str) -> time:
    """Parse 'HH:MM' into a datetime.time object."""
    h, m = t.split(":")
    return time(int(h), int(m))


def is_quiet_hours(start: str, end: str, now: datetime | None = None) -> bool:
    """
    Return True if the current time falls within the quiet hours window.

    Handles cross-midnight windows (e.g., 22:00–08:00).
    `now` is injectable for testing; defaults to current local time.
    """
    if now is None:
        now = datetime.now()

    current = now.time().replace(second=0, microsecond=0)
    start_t = _parse_time(start)
    end_t = _parse_time(end)

    if start_t <= end_t:
        # Same-day window (e.g., 02:00–06:00)
        return start_t <= current < end_t
    else:
        # Cross-midnight window (e.g., 22:00–08:00)
        return current >= start_t or current < end_t
