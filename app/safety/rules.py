"""
Deterministic keyword/phrase rules for known critical situations.

These run BEFORE any ML classifier — they are fast, transparent, and cover the cases
where we must never miss (false negative on crisis is more dangerous than false positive).

Design principle: rules are permissive at the detection stage.
Downstream risk_scoring.py applies final tier assignment.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.safety.patterns import scan


@dataclass
class RuleResult:
    """Output of the rules pass."""
    flagged: bool
    matched_groups: dict[str, list[str]] = field(default_factory=dict)

    @property
    def has_self_harm(self) -> bool:
        return "self_harm" in self.matched_groups

    @property
    def has_crisis(self) -> bool:
        return "crisis" in self.matched_groups

    @property
    def has_danger(self) -> bool:
        return "danger" in self.matched_groups


def evaluate(text: str) -> RuleResult:
    """
    Apply all regex/keyword rules to `text`.

    Returns a RuleResult — downstream code should combine this with
    classifier output in risk_scoring.py before making routing decisions.
    """
    matches = scan(text)
    return RuleResult(flagged=bool(matches), matched_groups=matches)
