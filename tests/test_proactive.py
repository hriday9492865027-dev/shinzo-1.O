"""
Tests for the proactive engine (quiet hours, decision engine, frequency guard).
"""
import os
from datetime import datetime

import pytest

os.environ.setdefault("LLM_PROVIDER", "mock")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")


@pytest.mark.parametrize("start,end,now_time,expected", [
    # Cross-midnight window (22:00–08:00)
    ("22:00", "08:00", datetime(2024, 1, 1, 23, 0), True),   # 23:00 is in quiet hours
    ("22:00", "08:00", datetime(2024, 1, 1, 7, 59), True),   # 07:59 is in quiet hours
    ("22:00", "08:00", datetime(2024, 1, 1, 12, 0), False),  # noon is not
    ("22:00", "08:00", datetime(2024, 1, 1, 8, 0), False),   # exactly 08:00 is not (exclusive end)
    # Same-day window (02:00–06:00)
    ("02:00", "06:00", datetime(2024, 1, 1, 3, 0), True),
    ("02:00", "06:00", datetime(2024, 1, 1, 7, 0), False),
])
def test_quiet_hours(start, end, now_time, expected):
    from app.proactive.quiet_hours import is_quiet_hours

    result = is_quiet_hours(start, end, now=now_time)
    assert result == expected, f"is_quiet_hours({start}, {end}, now={now_time.time()}) = {result}, expected {expected}"


def test_decision_do_nothing_during_quiet_hours(monkeypatch):
    from datetime import UTC, datetime, timedelta

    from app.proactive.decision_engine import evaluate

    monkeypatch.setenv("QUIET_HOURS_START", "00:00")
    monkeypatch.setenv("QUIET_HOURS_END", "23:59")
    monkeypatch.setenv("PROACTIVE_ENABLED", "true")

    # Force settings reload
    import app.core.config as config_module
    config_module.get_settings.cache_clear()

    result = evaluate(
        last_message_at=datetime.now(UTC) - timedelta(days=5),
        recent_proactive_count=0,
        pause_mode_active=False,
        follow_up_hook="check_in",
        message_count=10,
    )
    assert result.should_initiate is False
    config_module.get_settings.cache_clear()


def test_decision_do_nothing_when_disabled(monkeypatch):
    from datetime import UTC, datetime, timedelta

    from app.proactive.decision_engine import evaluate

    monkeypatch.setenv("PROACTIVE_ENABLED", "false")
    import app.core.config as config_module
    config_module.get_settings.cache_clear()

    result = evaluate(
        last_message_at=datetime.now(UTC) - timedelta(days=10),
        recent_proactive_count=0,
        pause_mode_active=False,
        follow_up_hook="check_in",
        message_count=20,
    )
    assert result.should_initiate is False
    config_module.get_settings.cache_clear()


def test_decision_do_nothing_pause_mode():
    from datetime import UTC, datetime, timedelta

    from app.proactive.decision_engine import evaluate

    result = evaluate(
        last_message_at=datetime.now(UTC) - timedelta(days=5),
        recent_proactive_count=0,
        pause_mode_active=True,
        follow_up_hook="check_in",
    )
    assert result.should_initiate is False
    assert "pause" in result.reason.lower()


def test_decision_do_nothing_frequency_guard():
    from datetime import UTC, datetime, timedelta

    from app.proactive.decision_engine import evaluate

    result = evaluate(
        last_message_at=datetime.now(UTC) - timedelta(days=5),
        recent_proactive_count=5,  # over limit
        pause_mode_active=False,
        follow_up_hook="check_in",
        message_count=10,
    )
    assert result.should_initiate is False
    assert "frequency" in result.reason.lower()
