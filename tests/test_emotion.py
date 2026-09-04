"""
Tests for the emotion engine (classifier + signal building).
Tests use the fallback path (no real model) so they run without torch/HF.
"""
import os

os.environ.setdefault("LLM_PROVIDER", "mock")


def test_build_signal_neutral_fallback():
    """When classifier is unavailable, signal defaults to neutral/not-distressed."""
    from app.emotion.signals import build_signal

    signal = build_signal("hey what's up")
    assert signal.primary_emotion in ("neutral", "joy", "sadness", "fear", "anger", "disgust", "surprise")
    assert 0.0 <= signal.confidence <= 1.0
    assert isinstance(signal.is_distressed, bool)


def test_emotion_signal_context_string_neutral():
    from app.emotion.signals import EmotionSignal

    sig = EmotionSignal(
        primary_emotion="neutral",
        confidence=0.9,
        is_significant=True,
        is_distressed=False,
    )
    # Neutral emotions should not produce a context string
    assert sig.to_context_string() == ""


def test_emotion_signal_context_string_distressed():
    from app.emotion.signals import EmotionSignal

    sig = EmotionSignal(
        primary_emotion="sadness",
        confidence=0.85,
        is_significant=True,
        is_distressed=True,
    )
    ctx = sig.to_context_string()
    assert "sadness" in ctx
    assert "distress" in ctx.lower()


def test_emotion_signal_not_significant():
    from app.emotion.signals import EmotionSignal

    sig = EmotionSignal(
        primary_emotion="anger",
        confidence=0.30,   # below SIGNIFICANCE_THRESHOLD
        is_significant=False,
        is_distressed=False,
    )
    assert sig.to_context_string() == ""
