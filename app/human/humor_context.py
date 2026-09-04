"""
Humor Context — determines whether humor or teasing is appropriate.

Humor is welcome in Shinzo's personality but must pass three conditions:
  1. Conversational energy is high enough (not heavy/distress)
  2. Relationship trust is sufficient (not with a brand-new user)
  3. The user's message doesn't signal a need for seriousness

This module returns a HumorContext that the social intent layer and
authenticity filter both consult.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.emotion.signals import EmotionSignal
from app.social.conversation_dynamics import ConversationDynamics
from app.social.relationship_state import RelationshipState


@dataclass
class HumorContext:
    humor_allowed: bool
    teasing_allowed: bool
    reason: str  # human-readable explanation for debugging

    def to_instruction(self) -> str:
        if self.teasing_allowed:
            return "Affectionate teasing is appropriate if it fits naturally."
        if self.humor_allowed:
            return "A light touch of humor is fine here if it arises naturally."
        return "Keep humor minimal or absent — the mood doesn't support it."


def evaluate(
    emotion: EmotionSignal,
    dynamics: ConversationDynamics,
    relationship: RelationshipState,
) -> HumorContext:
    """Evaluate whether humor/teasing is appropriate for this turn."""
    # Hard block on distress
    if emotion.is_distressed:
        return HumorContext(
            humor_allowed=False,
            teasing_allowed=False,
            reason="User is in distress — humor is inappropriate.",
        )

    if emotion.primary_emotion in ("sadness", "fear", "anger") and emotion.is_significant:
        return HumorContext(
            humor_allowed=False,
            teasing_allowed=False,
            reason=f"Significant {emotion.primary_emotion} signal.",
        )

    # Energy check
    if dynamics.energy < 0.30:
        return HumorContext(
            humor_allowed=False,
            teasing_allowed=False,
            reason="Conversation energy too low for humor.",
        )

    # Trust check for teasing
    teasing_ok = relationship.trust >= 0.40 and dynamics.energy >= 0.55
    humor_ok = dynamics.energy >= 0.40

    reason = f"energy={dynamics.energy:.2f}, trust={relationship.trust:.2f}"
    return HumorContext(humor_allowed=humor_ok, teasing_allowed=teasing_ok, reason=reason)
