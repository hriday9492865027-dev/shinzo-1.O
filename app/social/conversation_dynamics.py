"""
Conversation Dynamics — reads the current conversation's rhythm and energy.

Inputs: recent message history (last N turns)
Outputs: energy level, conversation depth, user verbosity, pacing

Used by:
  - RelationshipState.energy (overwritten here)
  - SocialIntent selection (energy influences whether humor/teasing is appropriate)
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ConversationDynamics:
    energy: float           # [0.0, 1.0] — low = quiet/heavy, high = lively/playful
    depth: float            # [0.0, 1.0] — surface chat vs. emotionally deep
    user_verbosity: float   # [0.0, 1.0] — avg message length ratio
    pace: str               # "slow" | "medium" | "fast"

    def to_context_string(self) -> str:
        parts = []
        if self.energy < 0.25:
            parts.append("Conversation energy is low — keep responses calm and short.")
        elif self.energy > 0.75:
            parts.append("Conversation energy is high — playfulness is appropriate.")
        if self.depth > 0.6:
            parts.append("This is an emotionally deep conversation — stay present.")
        if self.user_verbosity < 0.3:
            parts.append("User is sending short messages — mirror that brevity.")
        return " ".join(parts)


def analyze(recent_messages: list[dict]) -> ConversationDynamics:
    """
    Analyze a list of recent message dicts: [{"role": "user"|"shinzo", "content": "..."}]

    Returns ConversationDynamics based on message lengths, punctuation signals,
    and exclamation/emoji presence.
    """
    if not recent_messages:
        return ConversationDynamics(energy=0.5, depth=0.3, user_verbosity=0.5, pace="medium")

    user_msgs = [m["content"] for m in recent_messages if m.get("role") == "user"]
    if not user_msgs:
        return ConversationDynamics(energy=0.5, depth=0.3, user_verbosity=0.5, pace="medium")

    avg_length = sum(len(m) for m in user_msgs) / len(user_msgs)

    # Energy: exclamations, emoji, uppercase proportion
    exclamation_rate = sum(m.count("!") for m in user_msgs) / len(user_msgs)
    emoji_rate = sum(
        1 for m in user_msgs
        for ch in m if ord(ch) > 0x1F300
    ) / max(len(user_msgs), 1)
    energy = min(1.0, 0.5 + exclamation_rate * 0.15 + emoji_rate * 0.1)

    # Depth: question marks + words like "feel", "hurt", "afraid"
    depth_words = {"feel", "felt", "hurt", "scared", "afraid", "love", "hate", "alone", "miss"}
    depth_score = sum(
        1 for m in user_msgs
        for word in m.lower().split()
        if word in depth_words
    ) / max(len(user_msgs), 1)
    depth = min(1.0, depth_score * 0.3)

    # Verbosity
    verbosity = min(1.0, avg_length / 300)

    # Pace
    turn_count = len(recent_messages)
    if turn_count >= 10:
        pace = "fast"
    elif turn_count >= 5:
        pace = "medium"
    else:
        pace = "slow"

    return ConversationDynamics(
        energy=round(energy, 3),
        depth=round(depth, 3),
        user_verbosity=round(verbosity, 3),
        pace=pace,
    )
