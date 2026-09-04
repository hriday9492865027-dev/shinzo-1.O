"""
Proactive Decision Engine — answers: "Should Shinzo initiate a message right now?"

Decision factors:
  1. Proactive feature enabled (settings)
  2. Quiet hours not active
  3. Frequency guard not triggered (too many recent messages)
  4. Pause mode not set by user
  5. Sufficient inactivity gap (at least N hours since last message)
  6. Meaningful context exists (follow-up hook, shared memory, contextual event)

Returns a ProactiveDecision with INITIATE or DO_NOTHING + reason.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta

from app.core.config import get_settings
from app.proactive.quiet_hours import is_quiet_hours

MIN_INACTIVITY_HOURS = 18    # minimum gap before proactive is considered
MAX_MESSAGES_PER_DAY = 3     # frequency guard ceiling


@dataclass
class ProactiveDecision:
    should_initiate: bool
    reason: str
    hook: str = ""  # the context hook to use if initiating (e.g., "follow-up on interview")


def evaluate(
    last_message_at: datetime | None,
    recent_proactive_count: int,   # how many proactive messages sent in last 24h
    pause_mode_active: bool,
    follow_up_hook: str = "",      # set if there's something worth following up on
    message_count: int = 0,
    now: datetime | time | None = None,
) -> ProactiveDecision:
    """
    Evaluate whether Shinzo should initiate a message.
    """
    settings = get_settings()

    if not settings.proactive_enabled:
        return ProactiveDecision(False, "Proactive feature disabled in settings.")

    if pause_mode_active:
        return ProactiveDecision(False, "User set pause mode — no messages.")

    if is_quiet_hours(settings.quiet_hours_start, settings.quiet_hours_end, now=now):
        return ProactiveDecision(False, "Quiet hours active.")

    if recent_proactive_count >= MAX_MESSAGES_PER_DAY:
        return ProactiveDecision(
            False,
            f"Frequency guard: {recent_proactive_count} proactive messages sent today."
        )

    if last_message_at is None:
        return ProactiveDecision(False, "No message history — nothing to follow up on.")

    inactivity = datetime.now(UTC) - last_message_at
    if inactivity < timedelta(hours=MIN_INACTIVITY_HOURS):
        return ProactiveDecision(
            False,
            f"Only {inactivity.total_seconds() / 3600:.1f}h inactive — too soon."
        )

    # Check for meaningful context
    if follow_up_hook:
        return ProactiveDecision(True, "Follow-up hook available.", hook=follow_up_hook)

    # Generic check-in only if user has reasonable history
    if message_count >= 5 and inactivity >= timedelta(days=3):
        return ProactiveDecision(True, "Long inactivity + established history.", hook="check_in")

    return ProactiveDecision(False, "No compelling reason to initiate.")
