"""
Stage 1 — Normalization.
Cleans raw text records (whitespace, encoding artifacts, obvious formatting noise) before
validation. Kept deliberately simple/conservative: normalization should never change the meaning
or voice of an example, only clean mechanical noise.
"""
import re
import unicodedata


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_record(raw: dict) -> dict:
    """Normalizes the two free-text fields of a raw record dict in place-safe fashion."""
    normalized = dict(raw)
    for key in ("user_message", "shinzo_reply"):
        if key in normalized and isinstance(normalized[key], str):
            normalized[key] = normalize_text(normalized[key])
    return normalized
