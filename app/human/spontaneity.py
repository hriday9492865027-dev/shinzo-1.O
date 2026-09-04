"""
Spontaneity — adds contextual randomness to fight response templating.

Problems this solves:
  - Every reply starting with the same pattern ("Oh that's..." / "Hmm..." / "That sounds...")
  - Predictable question-at-end structure
  - Shinzo always taking the same conversational angle

Approach: on a small fraction of turns, inject a subtle nudge to vary the
response angle. This is a gentle instruction, not forced output.
"""
from __future__ import annotations

import random

_VARIATION_NUDGES = [
    "Try starting this reply mid-thought rather than with an opener.",
    "Be more direct than usual — get to the point in the first word.",
    "Use a shorter reply than you'd normally default to.",
    "Start with a specific observation before anything else.",
    "This one can be a little wry or understated.",
    "Let there be a bit of silence in this reply — don't fill every gap.",
    "Be warmer than the surface of the message requires.",
]

# Probability of injecting a variation nudge (15% of turns)
NUDGE_PROBABILITY = 0.15


def get_variation_nudge(seed: int | None = None) -> str:
    """
    Return a variation nudge with probability NUDGE_PROBABILITY.
    Returns empty string most of the time.
    `seed` can be set for deterministic testing.
    """
    rng = random.Random(seed) if seed is not None else random
    if rng.random() < NUDGE_PROBABILITY:
        return rng.choice(_VARIATION_NUDGES)
    return ""
