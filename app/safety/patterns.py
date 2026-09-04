"""
Regex pattern library for safety screening.

All patterns are pre-compiled at import time for performance.
Patterns are intentionally over-inclusive at the detection stage —
false positives are handled in risk_scoring.py by combining with
classifier confidence and contextual signals.
"""
from __future__ import annotations

import re

# ── Self-harm / suicidality ────────────────────────────────────────────────────
SELF_HARM_PATTERNS: list[re.Pattern] = [
    re.compile(r"\b(kill|killing)\s+(my)?self\b", re.IGNORECASE),
    re.compile(r"\b(want|wanted|wanna)\s+to\s+(die|end\s+it|disappear)\b", re.IGNORECASE),
    re.compile(r"\b(thinking|thought)\s+about\s+(suicide|ending\s+(my\s+)?life)\b", re.IGNORECASE),
    re.compile(r"\b(hurt|hurting|harm|harming|cut|cutting)\s+(my)?self\b", re.IGNORECASE),
    re.compile(r"\bsuicid(e|al|ally)\b", re.IGNORECASE),
    re.compile(r"\b(no\s+reason|not\s+worth\s+it)\s+to\s+(live|keep\s+going)\b", re.IGNORECASE),
    re.compile(r"\beveryone\s+would\s+be\s+better\s+off\s+without\s+me\b", re.IGNORECASE),
    re.compile(r"\b(overdose|od('d|ing)?)\b", re.IGNORECASE),
]

# ── Crisis / severe distress ───────────────────────────────────────────────────
CRISIS_PATTERNS: list[re.Pattern] = [
    re.compile(r"\bcan'?t\s+(go\s+on|keep\s+going|do\s+this\s+anymore)\b", re.IGNORECASE),
    re.compile(r"\b(completely|totally)\s+(numb|empty|hollow|broken)\b", re.IGNORECASE),
    re.compile(r"\bno\s+(hope|point|reason)\b", re.IGNORECASE),
    re.compile(r"\b(giving|given)\s+up\b", re.IGNORECASE),
    re.compile(r"\bfeel\s+(like\s+a\s+burden|worthless|trapped)\b", re.IGNORECASE),
]

# ── Abuse / danger ─────────────────────────────────────────────────────────────
DANGER_PATTERNS: list[re.Pattern] = [
    re.compile(r"\b(he|she|they)\s+(hit|hurt|beat|abused|choked)\s+(me)\b", re.IGNORECASE),
    re.compile(r"\b(physical|domestic)\s+(abuse|violence)\b", re.IGNORECASE),
    re.compile(r"\bi('m|\s+am)\s+(scared|afraid)\s+(of\s+him|of\s+her|to\s+go\s+home)\b", re.IGNORECASE),
]

ALL_PATTERNS: dict[str, list[re.Pattern]] = {
    "self_harm": SELF_HARM_PATTERNS,
    "crisis": CRISIS_PATTERNS,
    "danger": DANGER_PATTERNS,
}


def scan(text: str) -> dict[str, list[str]]:
    """
    Scan text against all pattern groups.
    Returns dict of group_name -> list of matched pattern strings.
    An empty dict means no matches (safe to proceed to next tier).
    """
    matches: dict[str, list[str]] = {}
    for group_name, patterns in ALL_PATTERNS.items():
        group_matches = [p.pattern for p in patterns if p.search(text)]
        if group_matches:
            matches[group_name] = group_matches
    return matches
