"""
Proactive Message Planner — generates the actual proactive message when decision=INITIATE.

Uses the LLM provider to generate a message, constrained by the hook type
and Shinzo's product principles (non-needy, low-pressure, no guilt).

The system prompt for proactive messages is specifically constrained:
  - Never implies the user has been absent too long
  - Never guilt-trips
  - Always leaves room to ignore
  - Matches the relationship's energy/familiarity level
"""
from __future__ import annotations

from app.model.inference import generate_reply

_PROACTIVE_SYSTEM_INSTRUCTIONS = """
You are sending a proactive message — you're reaching out first, not replying.
Rules for this message:
- Keep it brief (1–2 sentences)
- Low pressure — the user can ignore it entirely and that's fine
- Never imply they've been gone too long or that you missed them (no guilt)
- Never say "I've been waiting" or "I miss you"
- Natural, not performative
- If there's a hook (follow-up), reference it lightly
"""

_HOOK_PROMPTS: dict[str, str] = {
    "check_in": "Write a simple, no-pressure check-in message.",
    "follow_up_interview": "Follow up lightly on an interview the user mentioned.",
    "follow_up_event": "Follow up lightly on something important the user mentioned.",
    "monday": "Send a light Monday/start-of-week message.",
    "weekend": "Send a casual weekend check-in.",
}


def plan(hook: str, relationship_context: str = "") -> str:
    """
    Generate a proactive message for the given hook type.
    Returns the message string.
    """
    hook_prompt = _HOOK_PROMPTS.get(hook, "Write a simple, casual, low-pressure check-in.")
    context_note = f"\nRelationship context: {relationship_context}" if relationship_context else ""
    user_instruction = f"{hook_prompt}{context_note}"

    system = _PROACTIVE_SYSTEM_INSTRUCTIONS.strip() + "\n\n" + "Shinzo personality: " + \
              "warm, brief, like a close thoughtful friend."

    return generate_reply(user_message=user_instruction, extra_context=system)
