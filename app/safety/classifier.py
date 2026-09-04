"""
ML safety classifier — wraps a pretrained HF text-classification model.

Used as the second tier in the safety pipeline, after deterministic rules.
The classifier catches ambiguous-risk language that regex patterns miss.

Default model: cross-encoder/nli-deberta-v3-small used in a zero-shot setup
to avoid needing a purpose-specific safety model while still being more
nuanced than keyword matching.

Falls back gracefully to a NEUTRAL result if the model is unavailable
(preserves mock/rule-only operation in offline dev environments).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache

logger = logging.getLogger(__name__)

CANDIDATE_LABELS = ["safe", "distress", "self-harm", "crisis"]


@dataclass
class ClassifierResult:
    label: str          # top predicted label
    score: float        # confidence [0.0, 1.0]
    all_scores: dict[str, float]


@lru_cache(maxsize=1)
def _get_pipeline():
    """Lazy-load the zero-shot classification pipeline."""
    try:
        from transformers import pipeline as hf_pipeline
        return hf_pipeline(
            "zero-shot-classification",
            model="cross-encoder/nli-deberta-v3-small",
        )
    except Exception as exc:
        logger.warning("Safety classifier unavailable (%s). Falling back to rules-only.", exc)
        return None


def classify(text: str) -> ClassifierResult:
    """
    Run zero-shot safety classification on `text`.
    Returns NEUTRAL ('safe', score=0.0) if model is unavailable.
    """
    pipe = _get_pipeline()
    if pipe is None:
        return ClassifierResult(
            label="safe",
            score=0.0,
            all_scores={label: 0.0 for label in CANDIDATE_LABELS},
        )

    try:
        result = pipe(text, candidate_labels=CANDIDATE_LABELS, multi_label=False)
        scores_dict = dict(zip(result["labels"], result["scores"], strict=False))
        top_label = result["labels"][0]
        return ClassifierResult(
            label=top_label,
            score=result["scores"][0],
            all_scores=scores_dict,
        )
    except Exception as exc:
        logger.error("Safety classifier inference failed: %s", exc)
        return ClassifierResult(label="safe", score=0.0, all_scores={})
