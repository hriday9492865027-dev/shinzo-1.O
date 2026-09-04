"""
Scores memory candidates for relevance and importance before storage.

Scoring heuristics (0.0–1.0):
  - Length: very short candidates score lower (less information content)
  - Personal facts (named entities, relationships): higher score
  - Upcoming events: high score (time-sensitive, actionable)
  - Emotional salience markers (love, hate, devastated, thrilled): higher score
  - Generic statements without personal anchoring: lower score

Threshold: candidates below STORE_THRESHOLD are discarded.
"""
from __future__ import annotations

import re

STORE_THRESHOLD = 0.40  # candidates below this are not stored

# Signals that increase importance
_HIGH_IMPORTANCE_PATTERNS = [
    re.compile(r"\b(interview|surgery|exam|wedding|funeral|court|diagnosis)\b", re.IGNORECASE),
    re.compile(r"\b(broke\s+up|got\s+(fired|promoted|married|divorced|pregnant))\b", re.IGNORECASE),
    re.compile(r"\b(tomorrow|next\s+week|on\s+\w+day)\b", re.IGNORECASE),
]

_MEDIUM_IMPORTANCE_PATTERNS = [
    re.compile(r"\b(love|hate|can't\s+stand|obsessed\s+with|terrified\s+of)\b", re.IGNORECASE),
    re.compile(r"\bmy\s+(job|work|school|university|college|partner|boyfriend|girlfriend)\b", re.IGNORECASE),
]

_LOW_IMPORTANCE_SIGNALS = [
    re.compile(r"\b(today|just|recently|kind\s+of|sort\s+of)\b", re.IGNORECASE),
]


def score(candidate: str) -> float:
    """
    Score a memory candidate string in [0.0, 1.0].
    Higher = more important = more likely to be stored.
    """
    if not candidate:
        return 0.0

    s = 0.4  # base score

    # Length bonus (more information = slightly higher)
    length = len(candidate)
    if length > 80:
        s += 0.15
    elif length > 40:
        s += 0.08

    # High-importance signal
    for pattern in _HIGH_IMPORTANCE_PATTERNS:
        if pattern.search(candidate):
            s += 0.25
            break

    # Medium-importance signal
    for pattern in _MEDIUM_IMPORTANCE_PATTERNS:
        if pattern.search(candidate):
            s += 0.12
            break

    # Penalize very generic statements
    generic_penalty = sum(1 for p in _LOW_IMPORTANCE_SIGNALS if p.search(candidate))
    s -= generic_penalty * 0.05

    return min(max(round(s, 3), 0.0), 1.0)


def filter_candidates(candidates: list[str]) -> list[tuple[str, float]]:
    """
    Score all candidates and return those above STORE_THRESHOLD as (text, score) pairs.
    Sorted by score descending.
    """
    scored = [(c, score(c)) for c in candidates]
    filtered = [(c, s) for c, s in scored if s >= STORE_THRESHOLD]
    return sorted(filtered, key=lambda x: x[1], reverse=True)
