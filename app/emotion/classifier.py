"""
Emotion classifier — wraps the j-hartmann/emotion-english-distilroberta-base model.

Labels: anger, disgust, fear, joy, neutral, sadness, surprise
Model is lazy-loaded and cached. Falls back to NEUTRAL if unavailable.

Design constraint (from docs/PERSONALITY_SPEC.md):
  Emotion output is a SIGNAL, not a diagnosis. The signal informs response
  tone — it is never surfaced to the user ("I can tell you're feeling X").
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache

logger = logging.getLogger(__name__)

EMOTION_LABELS = ["anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise"]


@dataclass
class RawEmotionOutput:
    label: str
    score: float
    all_scores: dict[str, float]


@lru_cache(maxsize=1)
def _get_pipeline(model_name: str):
    try:
        from transformers import pipeline as hf_pipeline
        return hf_pipeline("text-classification", model=model_name, top_k=None)
    except Exception as exc:
        logger.warning("Emotion classifier unavailable (%s). Defaulting to neutral.", exc)
        return None


def classify(text: str, model_name: str = "j-hartmann/emotion-english-distilroberta-base") -> RawEmotionOutput:
    """
    Run emotion classification on text.
    Returns a RawEmotionOutput with the top label and all label scores.
    Falls back to neutral/0.0 if model unavailable.
    """
    pipe = _get_pipeline(model_name)
    if pipe is None:
        return RawEmotionOutput(
            label="neutral",
            score=1.0,
            all_scores={label: 0.0 for label in EMOTION_LABELS},
        )

    try:
        result = pipe(text[:512])  # truncate for efficiency
        # pipeline with top_k=None returns list of dicts per input
        label_scores = {item["label"]: item["score"] for item in result[0]}
        top = max(label_scores.items(), key=lambda kv: kv[1])
        return RawEmotionOutput(label=top[0], score=top[1], all_scores=label_scores)
    except Exception as exc:
        logger.error("Emotion inference failed: %s", exc)
        return RawEmotionOutput(label="neutral", score=1.0, all_scores={})
