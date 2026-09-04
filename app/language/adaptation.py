"""
Language Adaptation — applies a LanguageProfile to generation guidance.

This module does NOT force style — it produces a context instruction that
nudges the LLM to adapt naturally. The LLM may ignore subtle nudges,
which is correct behavior (authenticity > compliance).

Product constraint: never force code-switching. If the user writes in
Hinglish, Shinzo may naturally follow, but should never be instructed to
produce artificial bilingual mixing.
"""
from __future__ import annotations

from app.language.style_profile import LanguageProfile


def build_adaptation_instruction(profile: LanguageProfile) -> str:
    """
    Produce a context string for injection into the system prompt.
    Returns empty string if no meaningful adaptation is needed.
    """
    instruction = profile.to_instruction()
    if not instruction:
        return ""
    return f"Language/style adaptation guidance: {instruction}"
