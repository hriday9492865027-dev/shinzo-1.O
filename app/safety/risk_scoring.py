"""
Combines rule + classifier signals into a single RiskTier decision.

Tier definitions (from docs/SAFETY_POLICY.md):
  LOW    — no flags, or flags with very low classifier confidence
  MEDIUM — ambiguous signals (crisis / distress language, unclear intent)
  HIGH   — self-harm / suicidal ideation clearly present, or abuse danger

Downstream: response_routing.py uses the tier to decide the reply path.
"""
from __future__ import annotations

from app.api.schemas.common import RiskTier
from app.safety.classifier import ClassifierResult
from app.safety.rules import RuleResult

# Confidence threshold above which classifier label overrides absence of rule hits
CLASSIFIER_HIGH_THRESHOLD = 0.75
CLASSIFIER_MEDIUM_THRESHOLD = 0.50


def score(rule_result: RuleResult, classifier_result: ClassifierResult) -> RiskTier:
    """
    Combines rule flags and classifier output into a RiskTier.

    Logic (in precedence order):
    1. Self-harm rule hit → always HIGH
    2. Danger rule hit → always HIGH
    3. Classifier label=self-harm with high confidence → HIGH
    4. Crisis rule hit OR classifier label=crisis/distress with medium confidence → MEDIUM
    5. Otherwise → LOW
    """
    # Rule-based hard gates
    if rule_result.has_self_harm or rule_result.has_danger:
        return RiskTier.HIGH

    # Classifier overrides
    clf_label = classifier_result.label
    clf_score = classifier_result.score

    if clf_label == "self-harm" and clf_score >= CLASSIFIER_HIGH_THRESHOLD:
        return RiskTier.HIGH

    if rule_result.has_crisis:
        return RiskTier.MEDIUM

    if clf_label in ("crisis", "distress") and clf_score >= CLASSIFIER_MEDIUM_THRESHOLD:
        return RiskTier.MEDIUM

    return RiskTier.LOW
