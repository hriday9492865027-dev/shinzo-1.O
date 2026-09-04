"""
Authenticity Filter — final check before a reply is sent.

Detects and flags responses that fail the "plausible human friend" test:
  - Robotic openers ("I understand that...", "It sounds like...")
  - Therapeutic register ("It sounds like you're experiencing...")
  - Repetitive pattern (reply starts same as recent Shinzo replies)
  - Too long for the conversational context
  - Ends with a question when the rhythm guide said not to
  - Excessive affirmation ("Absolutely!", "Great!", "Of course!")

When a flag is detected, the orchestrator can:
  a) ask the LLM to refine (1 retry), or
  b) pass through if retry budget is exhausted

This module only DETECTS — it does not rewrite. Rewriting is done by
asking the LLM with a refinement instruction appended.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# Robotic opener patterns
_ROBOTIC_OPENERS = [
    re.compile(r"^i\s+understand\s+that\b", re.IGNORECASE),
    re.compile(r"^it\s+sounds\s+like\b", re.IGNORECASE),
    re.compile(r"^i('m|\s+am)\s+sorry\s+to\s+hear\b", re.IGNORECASE),
    re.compile(r"^that\s+(must\s+be|sounds)\s+(really\s+)?(hard|difficult|tough)\b", re.IGNORECASE),
    re.compile(r"^i\s+can\s+(understand|imagine|see)\s+how\b", re.IGNORECASE),
    re.compile(r"^absolutely[,!]", re.IGNORECASE),
    re.compile(r"^great[,!]", re.IGNORECASE),
    re.compile(r"^of\s+course[,!]", re.IGNORECASE),
    re.compile(r"^certainly[,!]", re.IGNORECASE),
]

# Therapeutic register patterns
_THERAPEUTIC_PATTERNS = [
    re.compile(r"\bit\s+sounds\s+like\s+you('re|\s+are)\s+experiencing\b", re.IGNORECASE),
    re.compile(r"\byou\s+might\s+want\s+to\s+consider\s+(seeing|talking\s+to)\b", re.IGNORECASE),
    re.compile(r"\bhave\s+you\s+considered\s+(therapy|speaking\s+with\s+a)\b", re.IGNORECASE),
]

# Max lengths (rough character counts) by target_length
_MAX_LENGTHS = {
    "very_short": 180,
    "short": 450,
    "medium": 900,
    "long": 2000,
}


@dataclass
class AuthenticityIssue:
    kind: str           # "robotic_opener" | "therapeutic" | "too_long" | "repetitive"
    detail: str


@dataclass
class AuthenticityResult:
    passed: bool
    issues: list[AuthenticityIssue] = field(default_factory=list)

    def refinement_instruction(self) -> str:
        """Returns instruction to append for LLM retry, if issues found."""
        if not self.issues:
            return ""
        descs = "; ".join(f"{i.kind}: {i.detail}" for i in self.issues)
        return (
            f"\n\n[Refinement needed — previous reply had: {descs}. "
            "Rewrite to sound more like a close friend and less like a script or therapist. "
            "Keep the same intent and warmth.]"
        )


def check(
    reply: str,
    target_length: str = "short",
    recent_shinzo_replies: list[str] | None = None,
) -> AuthenticityResult:
    """
    Check a generated reply for authenticity issues.

    Args:
        reply: the LLM-generated response
        target_length: from RhythmGuide ("very_short" | "short" | "medium" | "long")
        recent_shinzo_replies: last 3–5 Shinzo replies for repetition check
    """
    issues: list[AuthenticityIssue] = []
    stripped = reply.strip()

    # Check robotic openers
    for pattern in _ROBOTIC_OPENERS:
        if pattern.match(stripped):
            issues.append(AuthenticityIssue(
                kind="robotic_opener",
                detail=f"starts with '{stripped[:40]}'"
            ))
            break

    # Check therapeutic register
    for pattern in _THERAPEUTIC_PATTERNS:
        if pattern.search(stripped):
            issues.append(AuthenticityIssue(
                kind="therapeutic",
                detail=f"pattern matched: '{pattern.pattern[:50]}'"
            ))
            break

    # Check length
    max_len = _MAX_LENGTHS.get(target_length, 450)
    if len(stripped) > max_len:
        issues.append(AuthenticityIssue(
            kind="too_long",
            detail=f"{len(stripped)} chars vs {max_len} target for '{target_length}'"
        ))

    # Check repetition vs recent replies
    if recent_shinzo_replies:
        reply_start = stripped[:30].lower()
        for prev in recent_shinzo_replies[-3:]:
            if prev.strip()[:30].lower() == reply_start:
                issues.append(AuthenticityIssue(
                    kind="repetitive",
                    detail="starts the same as a recent reply"
                ))
                break

    return AuthenticityResult(passed=len(issues) == 0, issues=issues)
