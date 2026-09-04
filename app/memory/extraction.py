"""
Extracts memory candidates from a conversation turn.

Strategy (heuristic-first, LLM-assisted when available):
  - Named entity / personal fact patterns (name, job, location, relationship)
  - Stated feelings/opinions about significant events
  - Explicit preferences ("I love X", "I hate X", "I always/never Y")
  - Future events / commitments ("I have an interview next Thursday")

Returns a list of candidate strings. Downstream importance_scoring.py filters
and scores them before store.py writes the approved ones.
"""
from __future__ import annotations

import re

# Patterns that suggest a personally significant fact worth remembering
_MEMORY_PATTERNS = [
    # Personal facts
    re.compile(r"\bmy\s+(name\s+is|job\s+is|work\s+(at|as)|sister|brother|mom|dad|partner|boyfriend|girlfriend|wife|husband)\b", re.IGNORECASE),
    # Preferences
    re.compile(r"\bi\s+(love|hate|really\s+like|can't\s+stand|always|never)\s+\w", re.IGNORECASE),
    # Upcoming events
    re.compile(r"\bi\s+have\s+(an?\s+)?\w+(\s+\w+){0,3}\s+(tomorrow|next\s+\w+|on\s+\w+day|this\s+week)", re.IGNORECASE),
    # Recent significant events
    re.compile(r"\bi\s+(just|recently)\s+(broke\s+up|got\s+(a\s+job|fired|promoted|married|divorced)|moved|lost)\b", re.IGNORECASE),
    # Emotional disclosure about specific people
    re.compile(r"\b(my\s+(best\s+)?friend|my\s+partner|my\s+(mom|dad|sister|brother))\s+(is|has|said|did|keeps|told)\b", re.IGNORECASE),
]

# Minimum length for a candidate to be worth considering
MIN_CANDIDATE_LENGTH = 15


def extract(user_message: str) -> list[str]:
    """
    Extract memory candidates from a single user message.
    Returns a (possibly empty) list of candidate strings.
    Each candidate is the full sentence containing the match.
    """
    if not user_message or len(user_message) < MIN_CANDIDATE_LENGTH:
        return []

    # Split into rough sentences
    sentences = re.split(r"(?<=[.!?])\s+|(?<=\n)", user_message.strip())
    candidates: list[str] = []

    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < MIN_CANDIDATE_LENGTH:
            continue
        for pattern in _MEMORY_PATTERNS:
            if pattern.search(sentence):
                if sentence not in candidates:
                    candidates.append(sentence)
                break  # one match per sentence is enough

    return candidates
