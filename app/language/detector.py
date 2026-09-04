"""
Language Detector — detects the primary language of a user's message
and identifies code-switching patterns.

Uses lingua-language-detector for accuracy on short texts.
Falls back gracefully to "en" (English) if lingua is not installed.
"""
from __future__ import annotations

import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

_SUPPORTED_LANGUAGES = {"en", "es", "fr", "de", "pt", "hi", "ja", "ko", "zh"}


@lru_cache(maxsize=1)
def _get_detector():
    try:
        from lingua import LanguageDetectorBuilder
        detector = (
            LanguageDetectorBuilder
            .from_all_languages()
            .with_minimum_relative_distance(0.15)
            .build()
        )
        return detector
    except ImportError:
        logger.warning("lingua-language-detector not installed. Defaulting to 'en'.")
        return None


def detect_language(text: str) -> str:
    """
    Detect the primary language of `text`.
    Returns an ISO 639-1 code (e.g., 'en', 'es', 'hi').
    Returns 'en' if detection fails or lingua is unavailable.
    """
    if not text or len(text.strip()) < 5:
        return "en"

    detector = _get_detector()
    if detector is None:
        return "en"

    try:
        lang = detector.detect_language_of(text)
        if lang is None:
            return "en"
        iso = lang.iso_code_639_1.name.lower()
        return iso if len(iso) == 2 else "en"
    except Exception as exc:
        logger.debug("Language detection failed: %s", exc)
        return "en"


def detect_code_switching(texts: list[str]) -> bool:
    """
    Detect if the user is switching between languages across recent messages.
    Returns True if two or more distinct languages are detected.
    """
    if len(texts) < 2:
        return False
    langs = {detect_language(t) for t in texts if t.strip()}
    return len(langs) >= 2
