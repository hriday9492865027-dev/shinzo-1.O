"""
Text → vector embedding utility shared by memory and RAG modules.

Uses sentence-transformers (all-MiniLM-L6-v2 by default: 384-dim, fast, excellent
for semantic similarity). Model is lazy-loaded and cached per process.

Falls back gracefully to a zero vector if sentence-transformers is not installed
(keeps mock/rule-only dev lightweight).
"""
from __future__ import annotations

import logging
from functools import lru_cache

import numpy as np

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384  # dimension of all-MiniLM-L6-v2 output


@lru_cache(maxsize=1)
def _get_model():
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(EMBEDDING_MODEL)
        logger.info("Loaded embedding model: %s", EMBEDDING_MODEL)
        return model
    except Exception as exc:
        logger.warning("sentence-transformers unavailable (%s). Returning zero vectors.", exc)
        return None


def embed(text: str) -> np.ndarray:
    """
    Embed a single text string → 1-D float32 numpy array of length EMBEDDING_DIM.
    Returns a zero vector if the model is unavailable.
    """
    model = _get_model()
    if model is None:
        return np.zeros(EMBEDDING_DIM, dtype=np.float32)
    return model.encode(text, convert_to_numpy=True).astype(np.float32)


def embed_batch(texts: list[str]) -> np.ndarray:
    """
    Embed a list of texts → 2-D float32 array of shape (len(texts), EMBEDDING_DIM).
    """
    model = _get_model()
    if model is None:
        return np.zeros((len(texts), EMBEDDING_DIM), dtype=np.float32)
    return model.encode(texts, convert_to_numpy=True, batch_size=32).astype(np.float32)
