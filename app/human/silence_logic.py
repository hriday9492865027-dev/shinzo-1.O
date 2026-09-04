"""
Silence Logic — decides when brevity or near-silence is the right response.

Shinzo doesn't need to fill every gap. Sometimes the most human response
is a very short acknowledgment, or just holding space.

This module outputs a SilenceDecision:
  - should_be_brief: True → RhythmGuide should target "very_short"
  - reason: why

Called before interaction planning — can override the default rhythm.
"""
from __future__ import annotations

from dataclasses import dataclass

_BREVITY_TRIGGERS = {
    # Messages that are completions, not conversation starters
    "ok", "okay", "k", "lol", "haha", "hahaha", "😂", "😭", "💀",
    "thanks", "thank you", "ty", "thx",
    "ugh", "oof", "hmm", "hm",
    "yeah", "yep", "yup", "nope", "nah",
    "sure", "fine", "I'm fine", "im fine",
    "idk", "idc", "lmao", "omg",
}

_SILENCE_TRIGGERS = {
    # Explicit requests for no response
    "never mind", "nvm", "forget it", "forget it.",
    "I don't want to talk", "leave me alone", "i don't wanna talk",
}


@dataclass
class SilenceDecision:
    should_be_brief: bool
    should_stay_silent: bool  # True = don't respond at all (proactive holdoff)
    reason: str


def evaluate(user_message: str) -> SilenceDecision:
    """
    Evaluate whether the message calls for brevity or silence.
    """
    stripped = user_message.strip().lower().rstrip(".")

    if stripped in _SILENCE_TRIGGERS:
        return SilenceDecision(
            should_be_brief=True,
            should_stay_silent=True,
            reason="User signaled they don't want to engage.",
        )

    if stripped in _BREVITY_TRIGGERS or len(stripped) < 6:
        return SilenceDecision(
            should_be_brief=True,
            should_stay_silent=False,
            reason=f"Short/low-effort message: '{stripped}'",
        )

    return SilenceDecision(should_be_brief=False, should_stay_silent=False, reason="")
