"""
Social Intelligence — Relationship State

Tracks the evolving Shinzo–user relationship dynamic over time.
This state is reconstructed from DB memory on each request (no global mutable state).

State dimensions:
  familiarity    — how much history exists (0=new, 1=deeply known)
  trust          — willingness to be vulnerable (inferred from emotional openness)
  energy         — conversational energy level (mirrors recent message tone)
  recency        — how recent the last interaction was (decays over time)
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta


@dataclass
class RelationshipState:
    familiarity: float = 0.0   # [0.0, 1.0]
    trust: float = 0.0         # [0.0, 1.0]
    energy: float = 0.5        # [0.0, 1.0] — 0=very low, 1=very high
    recency: float = 1.0       # [0.0, 1.0] — decays with inactivity
    message_count: int = 0

    def to_context_string(self) -> str:
        """Brief string for context_builder. Only injects when meaningful."""
        parts = []
        if self.familiarity > 0.6:
            parts.append("We have a lot of shared history.")
        elif self.familiarity > 0.3:
            parts.append("We've talked a decent amount.")
        if self.trust > 0.6:
            parts.append("This person opens up fairly readily.")
        if self.energy < 0.25:
            parts.append("Their energy is low right now — match that.")
        elif self.energy > 0.75:
            parts.append("Their energy is high — it's okay to be playful.")
        if self.recency < 0.3:
            parts.append("It's been a while since we last spoke.")
        return " ".join(parts)


def build_state(
    message_count: int,
    emotion_is_distressed: bool,
    last_active_at: datetime | None,
    memory_count: int,
) -> RelationshipState:
    """
    Construct a RelationshipState from signals available at request time.
    All inputs are cheap to gather from DB.
    """
    familiarity = min(1.0, (message_count / 200) + (memory_count / 50) * 0.3)
    trust = min(1.0, familiarity * 0.7 + (0.3 if emotion_is_distressed else 0.0))

    # Recency decay: full at <1 hour, half at 3 days, near-zero at 2+ weeks
    if last_active_at is None:
        recency = 0.5
    else:
        delta = datetime.now(UTC) - last_active_at
        if delta < timedelta(hours=1):
            recency = 1.0
        elif delta < timedelta(days=3):
            recency = max(0.3, 1.0 - delta.total_seconds() / (3 * 86400))
        else:
            recency = max(0.0, 0.3 - (delta.days - 3) / 30)

    return RelationshipState(
        familiarity=round(familiarity, 3),
        trust=round(trust, 3),
        energy=0.5,  # overwritten by conversation_dynamics.py
        recency=round(recency, 3),
        message_count=message_count,
    )
