"""
Converts raw classifier scores into a structured EmotionSignal used downstream.

EmotionSignal is consumed by:
  - app/core/context_builder.py (informs response tone)
  - app/social/social_intent.py (influences intent selection)
  - app/human/authenticity_filter.py (guards against mismatched tone)

NEVER surfaced to the user directly as a label or diagnosis.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.emotion.classifier import RawEmotionOutput, classify

# Threshold above which an emotion is treated as "present and significant"
SIGNIFICANCE_THRESHOLD = 0.45

# Emotions that indicate the user may be in distress (for safety/social tuning)
DISTRESS_EMOTIONS = {"sadness", "fear", "anger"}

# Score threshold for marking as_distressed
DISTRESS_SCORE_THRESHOLD = 0.60


@dataclass
class EmotionSignal:
    """Structured emotion signal passed to downstream modules."""
    primary_emotion: str               # top-1 label from classifier
    confidence: float                  # 0.0–1.0
    is_significant: bool               # True if confidence >= SIGNIFICANCE_THRESHOLD
    is_distressed: bool                # True if distress emotion with high confidence
    all_scores: dict[str, float] = field(default_factory=dict)

    def to_context_string(self) -> str:
        """
        Produces a brief string for injection into context_builder.
        Returns empty string for neutral/low-confidence signals.
        """
        if not self.is_significant or self.primary_emotion == "neutral":
            return ""
        distress_note = " User may be in distress." if self.is_distressed else ""
        return (
            f"Emotional tone detected: {self.primary_emotion} "
            f"(confidence {self.confidence:.0%}).{distress_note} "
            "Adjust response warmth and pacing accordingly — do NOT name this emotion to the user."
        )


def build_signal(text: str, model_name: str = "j-hartmann/emotion-english-distilroberta-base") -> EmotionSignal:
    """
    Full pipeline: classify text → build EmotionSignal.
    """
    raw: RawEmotionOutput = classify(text, model_name=model_name)
    is_significant = raw.score >= SIGNIFICANCE_THRESHOLD
    is_distressed = (
        raw.label in DISTRESS_EMOTIONS
        and raw.score >= DISTRESS_SCORE_THRESHOLD
    )
    return EmotionSignal(
        primary_emotion=raw.label,
        confidence=raw.score,
        is_significant=is_significant,
        is_distressed=is_distressed,
        all_scores=raw.all_scores,
    )
