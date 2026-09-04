"""
Language Style Profile — builds a per-user LanguageProfile from message history.

Profile dimensions:
  primary_language   — ISO 639-1 code
  formality          — [0.0, 1.0] (0=very casual/slang, 1=formal)
  emoji_use          — [0.0, 1.0] (proportion of messages with emoji)
  avg_message_length — average characters per message
  code_switching     — True if user mixes languages

The profile informs language adaptation without forcing style changes.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.language.detector import detect_code_switching, detect_language

_SLANG_MARKERS = {
    "lol", "lmao", "omg", "tbh", "ngl", "imo", "smh", "idk", "bruh",
    "fr", "lowkey", "highkey", "vibe", "slay", "periodt", "bet",
}

_FORMAL_MARKERS = {
    "however", "therefore", "furthermore", "additionally", "consequently",
    "regarding", "concerning", "pursuant", "wherein",
}


@dataclass
class LanguageProfile:
    primary_language: str = "en"
    formality: float = 0.5          # [0.0, 1.0]
    emoji_use: float = 0.0          # [0.0, 1.0]
    avg_message_length: float = 80.0
    code_switching: bool = False
    slang_frequency: float = 0.0    # [0.0, 1.0]

    def to_instruction(self) -> str:
        """Brief style instruction for the LLM."""
        parts = []
        if self.primary_language != "en":
            parts.append(f"The user writes primarily in {self.primary_language} — mirror that language.")
        if self.code_switching:
            parts.append("They mix languages — follow their lead naturally, don't force it.")
        if self.formality < 0.30:
            parts.append("They write very casually — match that informality.")
        elif self.formality > 0.70:
            parts.append("They write formally — avoid being too casual.")
        if self.emoji_use > 0.50:
            parts.append("They use emoji — occasional emoji is appropriate.")
        if self.avg_message_length < 40:
            parts.append("They message briefly — match their conciseness.")
        return " ".join(parts)


def build_profile(recent_messages: list[str]) -> LanguageProfile:
    """
    Build a LanguageProfile from a list of recent user message strings.
    """
    if not recent_messages:
        return LanguageProfile()

    valid = [m for m in recent_messages if m.strip()]
    if not valid:
        return LanguageProfile()

    # Primary language
    lang = detect_language(valid[-1]) if valid else "en"

    # Code switching
    code_switch = detect_code_switching(valid[-5:]) if len(valid) >= 2 else False

    # Emoji use
    emoji_count = sum(1 for m in valid for ch in m if ord(ch) > 0x1F300)
    emoji_use = min(1.0, emoji_count / max(len(valid), 1))

    # Average length
    avg_len = sum(len(m) for m in valid) / len(valid)

    # Formality
    words = " ".join(valid).lower().split()
    word_set = set(words)
    slang_hits = len(word_set & _SLANG_MARKERS) / max(len(word_set), 1)
    formal_hits = len(word_set & _FORMAL_MARKERS) / max(len(word_set), 1)
    formality = min(1.0, max(0.0, 0.5 + formal_hits * 5 - slang_hits * 5))

    return LanguageProfile(
        primary_language=lang,
        formality=round(formality, 3),
        emoji_use=round(emoji_use, 3),
        avg_message_length=round(avg_len, 1),
        code_switching=code_switch,
        slang_frequency=round(slang_hits, 3),
    )
