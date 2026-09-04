"""
Conversation Rhythm — controls response length and pacing guidance.

Shinzo's default is short (1–3 sentences for casual/venting).
Longer structured replies are reserved for explicit advice requests.

This module translates conversation state into a length/pacing instruction
for the LLM.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.social.conversation_dynamics import ConversationDynamics
from app.social.social_intent import SocialIntent


@dataclass
class RhythmGuide:
    target_length: str      # "very_short" | "short" | "medium" | "long"
    pacing_note: str        # human-readable instruction for the LLM

    def to_instruction(self) -> str:
        length_map = {
            "very_short": "1–2 sentences maximum.",
            "short": "1–3 sentences. Don't pad.",
            "medium": "A few sentences — enough to cover it, not more.",
            "long": "This warrants a fuller response — structure is okay here.",
        }
        base = length_map.get(self.target_length, "Keep it natural.")
        if self.pacing_note:
            return f"{base} {self.pacing_note}"
        return base


def guide(intent: SocialIntent, dynamics: ConversationDynamics) -> RhythmGuide:
    """
    Return a RhythmGuide for the current turn based on intent and dynamics.
    """
    if intent == SocialIntent.GIVE_SPACE:
        return RhythmGuide(
            target_length="very_short",
            pacing_note="Match their low energy. One sentence is fine.",
        )

    if intent == SocialIntent.ADVISE:
        return RhythmGuide(
            target_length="long",
            pacing_note="Structure is okay. Cover what's needed, then stop.",
        )

    if intent in (SocialIntent.LISTEN, SocialIntent.CHECK_IN):
        return RhythmGuide(
            target_length="short",
            pacing_note="Don't over-explain. Just be present.",
        )

    if intent in (SocialIntent.TEASE, SocialIntent.JOKE, SocialIntent.CELEBRATE):
        return RhythmGuide(
            target_length="short",
            pacing_note="Brevity makes humor land better.",
        )

    # Default: mirror user verbosity
    if dynamics.user_verbosity < 0.25:
        return RhythmGuide(target_length="very_short", pacing_note="They're brief — be brief.")
    if dynamics.user_verbosity > 0.70:
        return RhythmGuide(target_length="medium", pacing_note="")

    return RhythmGuide(target_length="short", pacing_note="")
