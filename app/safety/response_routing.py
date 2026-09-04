"""
Safety response routing — maps a RiskTier to a response path.

Routing decisions:
  LOW    → normal pipeline (orchestrator continues as usual)
  MEDIUM → insert a soft acknowledgment/check-in prefix into the context,
           ask the LLM to be especially present and non-advice-giving
  HIGH   → return a hard-coded compassionate response + crisis resource,
           do NOT route to LLM (avoids any chance of an unhelpful generation)

This module only returns routing instructions — it does NOT generate text itself.
The orchestrator in app/core/orchestrator.py reads these instructions and acts.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.api.schemas.common import RiskTier

# Crisis resource line — configurable to region
CRISIS_LINE = "988 (US Suicide & Crisis Lifeline — call or text)"
CRISIS_INTERNATIONAL = "findahelpline.com for international resources"

HIGH_RISK_REPLY = (
    "Thank you for telling me — that took something real. "
    "Are you safe right now? I want to make sure you have support "
    "beyond this conversation. Please consider reaching out to a crisis line: "
    f"{CRISIS_LINE}. {CRISIS_INTERNATIONAL}. I'm here with you."
)

MEDIUM_RISK_CONTEXT_INJECTION = (
    "The user may be experiencing significant distress. "
    "Be fully present. Do not give advice or a checklist. "
    "Ask one gentle, open question to understand what they need. "
    "If self-harm or safety is a concern, ask directly and gently."
)


@dataclass
class RoutingDecision:
    tier: RiskTier
    short_circuit: bool          # if True, use `fixed_reply` and skip LLM entirely
    fixed_reply: str = ""        # only used when short_circuit=True
    context_injection: str = ""  # additional safety context injected into the system prompt


def route(tier: RiskTier) -> RoutingDecision:
    """Translate a RiskTier into a RoutingDecision consumed by the orchestrator."""
    if tier == RiskTier.HIGH:
        return RoutingDecision(
            tier=tier,
            short_circuit=True,
            fixed_reply=HIGH_RISK_REPLY,
        )
    if tier == RiskTier.MEDIUM:
        return RoutingDecision(
            tier=tier,
            short_circuit=False,
            context_injection=MEDIUM_RISK_CONTEXT_INJECTION,
        )
    # LOW
    return RoutingDecision(tier=tier, short_circuit=False)
