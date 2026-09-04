"""
Tests for the safety module (rules, risk scoring, response routing).
"""
import os

import pytest

os.environ.setdefault("LLM_PROVIDER", "mock")


@pytest.mark.parametrize("text,should_flag", [
    ("I want to kill myself", True),
    ("thinking about suicide", True),
    ("I've been hurting myself", True),
    ("everyone would be better off without me", True),
    ("I had a great day at work", False),
    ("hey what's up", False),
    ("I'm a bit sad today", False),
])
def test_rules_flagging(text, should_flag):
    from app.safety.rules import evaluate

    result = evaluate(text)
    assert result.flagged == should_flag, f"'{text}' flagged={result.flagged}, expected={should_flag}"


def test_self_harm_rule_sets_correct_group():
    from app.safety.rules import evaluate

    result = evaluate("I've been cutting myself")
    assert result.has_self_harm is True


def test_danger_rule():
    from app.safety.rules import evaluate

    result = evaluate("he hit me and I'm scared to go home")
    assert result.has_danger is True


def test_risk_scoring_high_on_self_harm():
    from app.api.schemas.common import RiskTier
    from app.safety.classifier import ClassifierResult
    from app.safety.risk_scoring import score
    from app.safety.rules import RuleResult

    rule_result = RuleResult(flagged=True, matched_groups={"self_harm": ["pattern"]})
    clf_result = ClassifierResult(label="safe", score=0.1, all_scores={})
    tier = score(rule_result, clf_result)
    assert tier == RiskTier.HIGH


def test_risk_scoring_low_on_safe_text():
    from app.api.schemas.common import RiskTier
    from app.safety.classifier import ClassifierResult
    from app.safety.risk_scoring import score
    from app.safety.rules import RuleResult

    rule_result = RuleResult(flagged=False, matched_groups={})
    clf_result = ClassifierResult(label="safe", score=0.95, all_scores={})
    tier = score(rule_result, clf_result)
    assert tier == RiskTier.LOW


def test_high_risk_routing_short_circuits():
    from app.api.schemas.common import RiskTier
    from app.safety.response_routing import route

    decision = route(RiskTier.HIGH)
    assert decision.short_circuit is True
    assert "988" in decision.fixed_reply or "crisis" in decision.fixed_reply.lower()


def test_low_risk_routing_passes_through():
    from app.api.schemas.common import RiskTier
    from app.safety.response_routing import route

    decision = route(RiskTier.LOW)
    assert decision.short_circuit is False
    assert decision.context_injection == ""


def test_medium_risk_routing_injects_context():
    from app.api.schemas.common import RiskTier
    from app.safety.response_routing import route

    decision = route(RiskTier.MEDIUM)
    assert decision.short_circuit is False
    assert len(decision.context_injection) > 0
