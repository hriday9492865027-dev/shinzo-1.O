"""
Social Intent Selection — chooses what Shinzo's response should *do*, not just say.

The 12 intents (from docs/PRODUCT_VISION.md):
  listen            — reflect/hold without driving
  continue_topic    — stay on the current subject
  ask               — ask one meaningful question
  observe           — make a gentle observation
  tease             — light playful teasing (only when energy/trust support it)
  joke              — introduce humor
  change_subject    — redirect when current topic feels exhausted
  reference_moment  — naturally bring back a shared reference/memory
  check_in          — low-key check on how they're doing
  celebrate         — acknowledge good news warmly
  give_space        — very short or near-silent response
  advise            — structured help (ONLY when explicitly requested)

Intent is a planning signal to interaction_planner.py — it constrains the
LLM's output shape without writing the response for it.
"""
from __future__ import annotations

from enum import Enum

from app.emotion.signals import EmotionSignal
from app.social.conversation_dynamics import ConversationDynamics
from app.social.relationship_state import RelationshipState


class SocialIntent(str, Enum):
    LISTEN = "listen"
    CONTINUE_TOPIC = "continue_topic"
    ASK = "ask"
    OBSERVE = "observe"
    TEASE = "tease"
    JOKE = "joke"
    CHANGE_SUBJECT = "change_subject"
    REFERENCE_MOMENT = "reference_moment"
    CHECK_IN = "check_in"
    CELEBRATE = "celebrate"
    GIVE_SPACE = "give_space"
    ADVISE = "advise"


_ADVICE_KEYWORDS = {
    "what should i", "what do i do", "how do i", "advice", "suggest",
    "help me figure", "what would you", "tips", "options",
}


def _user_wants_advice(message: str) -> bool:
    lower = message.lower()
    return any(kw in lower for kw in _ADVICE_KEYWORDS)


def select(
    user_message: str,
    emotion: EmotionSignal,
    dynamics: ConversationDynamics,
    relationship: RelationshipState,
    has_shared_memory: bool = False,
) -> SocialIntent:
    """
    Select the most appropriate social intent for the current turn.

    Priority order:
    1. Explicit advice request → ADVISE
    2. Very short / low-effort message → GIVE_SPACE
    3. High distress → LISTEN
    4. Celebratory tone → CELEBRATE
    5. High energy + good trust → TEASE or JOKE
    6. Has relevant shared memory → REFERENCE_MOMENT
    7. Deep conversation → OBSERVE or ASK
    8. Default → CONTINUE_TOPIC
    """
    msg_len = len(user_message.strip())

    if _user_wants_advice(user_message):
        return SocialIntent.ADVISE

    if msg_len < 15:
        return SocialIntent.GIVE_SPACE

    if emotion.is_distressed:
        return SocialIntent.LISTEN

    if emotion.primary_emotion == "joy" and emotion.is_significant:
        return SocialIntent.CELEBRATE

    if dynamics.energy > 0.70 and relationship.trust > 0.40:
        # Alternate between tease and joke to avoid being one-note
        return SocialIntent.TEASE if relationship.message_count % 2 == 0 else SocialIntent.JOKE

    if has_shared_memory and relationship.familiarity > 0.35:
        return SocialIntent.REFERENCE_MOMENT

    if dynamics.depth > 0.50:
        return SocialIntent.OBSERVE if relationship.message_count % 3 != 0 else SocialIntent.ASK

    return SocialIntent.CONTINUE_TOPIC
