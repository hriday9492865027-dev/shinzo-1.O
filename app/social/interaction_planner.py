"""
Interaction Planner — translates a SocialIntent into concrete instructions
injected into the system prompt for the LLM.

The planner does NOT write the response — it writes planning constraints
that shape the LLM's behavior for this turn.
"""
from __future__ import annotations

from app.social.social_intent import SocialIntent

# Map each intent to a concise LLM instruction string
_INTENT_INSTRUCTIONS: dict[SocialIntent, str] = {
    SocialIntent.LISTEN: (
        "Just listen and reflect. Don't give advice, don't ask questions. "
        "Show you understand without redirecting."
    ),
    SocialIntent.CONTINUE_TOPIC: (
        "Stay with the topic they raised. Engage naturally."
    ),
    SocialIntent.ASK: (
        "Ask exactly ONE meaningful question about something they actually raised. "
        "Don't end every reply with a question — only when it genuinely opens something."
    ),
    SocialIntent.OBSERVE: (
        "Make one gentle, specific observation about what they said. "
        "Frame it tentatively, not as certainty."
    ),
    SocialIntent.TEASE: (
        "Light, affectionate teasing is appropriate here. "
        "Never at their expense — tease the situation, the choice, the absurdity, not them."
    ),
    SocialIntent.JOKE: (
        "It's okay to be funny. Keep it natural, don't force it. "
        "A short, unexpected observation beats a setup-punchline joke."
    ),
    SocialIntent.CHANGE_SUBJECT: (
        "This topic feels exhausted. Find a natural pivot — "
        "connect to something they mentioned earlier or something adjacent."
    ),
    SocialIntent.REFERENCE_MOMENT: (
        "Naturally weave in something from earlier in the conversation or a shared memory. "
        "Don't make it obvious you're doing it — just let it arise organically."
    ),
    SocialIntent.CHECK_IN: (
        "This is a low-key check-in. Keep it brief, low pressure, "
        "no guilt for not replying sooner."
    ),
    SocialIntent.CELEBRATE: (
        "They have good news. Be genuinely warm about it — "
        "specific and brief, not effusive. Ask one question if you're curious."
    ),
    SocialIntent.GIVE_SPACE: (
        "Their message is short or low-energy. Match it — keep your reply very brief. "
        "One or two sentences maximum."
    ),
    SocialIntent.ADVISE: (
        "They've explicitly asked for advice or help deciding something. "
        "Give structured, useful guidance. This is the one situation where a list is okay. "
        "Still keep it human, not corporate."
    ),
}


def plan(intent: SocialIntent) -> str:
    """
    Return the LLM instruction string for a given intent.
    This string is injected into the system prompt by context_builder.py.
    """
    return _INTENT_INSTRUCTIONS.get(intent, "Respond naturally.")
