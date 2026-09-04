"""
Decision Router — determines the ConversationMode for the current turn.

ConversationMode influences how the orchestrator weights each module's output
and which response style is appropriate.

Modes (from app/api/schemas/common.py):
  CASUAL, FUN, VENTING, ADVICE, EMOTIONAL, REFLECTIVE, LONELY, CRISIS, CELEBRATION, SILENT
"""
from __future__ import annotations

from app.api.schemas.common import ConversationMode, RiskTier
from app.emotion.signals import EmotionSignal
from app.safety.rules import RuleResult
from app.social.social_intent import SocialIntent


def determine_mode(
    risk_tier: RiskTier,
    emotion: EmotionSignal,
    intent: SocialIntent,
    rule_result: RuleResult,
) -> ConversationMode:
    """
    Select the appropriate ConversationMode based on current turn signals.
    Priority: CRISIS > EMOTIONAL > VENTING > CELEBRATION > FUN > ADVICE > others
    """
    # Safety overrides all
    if risk_tier == RiskTier.HIGH or rule_result.has_self_harm:
        return ConversationMode.CRISIS

    if risk_tier == RiskTier.MEDIUM or rule_result.has_crisis:
        return ConversationMode.EMOTIONAL

    if emotion.is_distressed:
        return ConversationMode.VENTING

    if emotion.primary_emotion == "joy" and emotion.is_significant:
        return ConversationMode.CELEBRATION

    if intent == SocialIntent.ADVISE:
        return ConversationMode.ADVICE

    if intent in (SocialIntent.TEASE, SocialIntent.JOKE):
        return ConversationMode.FUN

    if intent == SocialIntent.GIVE_SPACE:
        return ConversationMode.SILENT

    if emotion.primary_emotion in ("sadness", "fear") and emotion.is_significant:
        return ConversationMode.LONELY

    return ConversationMode.CASUAL
