"""
FAISS index management for memory retrieval.

One index per user (identified by user_id). Indexes are built in-memory on
first query and optionally persisted to disk for warm restarts.

Index directory: ./shinzo_faiss_indexes/ (relative to process cwd).
Each user gets a file: <user_id>.index + <user_id>.ids.json

If FAISS is not installed, all operations are no-ops (zero results returned)
so the app degrades gracefully without vector search.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import numpy as np

from app.memory.embeddings import EMBEDDING_DIM

logger = logging.getLogger(__name__)

if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    INDEX_DIR = Path("/tmp/shinzo_faiss_indexes")
else:
    INDEX_DIR = Path("shinzo_faiss_indexes")


def _faiss():
    """Lazy import of faiss — returns None if not installed."""
    try:
        import faiss  # type: ignore
        return faiss
    except ImportError:
        return None


def _index_path(user_id: str) -> tuple[Path, Path]:
    try:
        INDEX_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        logger.warning("Could not create index dir %s: %s", INDEX_DIR, exc)
    return INDEX_DIR / f"{user_id}.index", INDEX_DIR / f"{user_id}.ids.json"


def build_index(user_id: str, vectors: np.ndarray, memory_ids: list[str]) -> bool:
    """
    Build (or rebuild) the FAISS flat L2 index for a user from scratch.
    vectors: shape (n, EMBEDDING_DIM)
    memory_ids: list of memory row UUIDs corresponding to each vector row.
    Returns True on success, False if FAISS unavailable.
    """
    faiss = _faiss()
    if faiss is None:
        logger.warning("FAISS not installed — memory index unavailable.")
        return False

    index = faiss.IndexFlatL2(EMBEDDING_DIM)
    index.add(vectors)

    index_path, ids_path = _index_path(user_id)
    faiss.write_index(index, str(index_path))
    with open(ids_path, "w") as f:
        json.dump(memory_ids, f)
    logger.debug("Built FAISS index for user %s: %d vectors", user_id, len(memory_ids))
    return True


def add_to_index(user_id: str, vector: np.ndarray, memory_id: str) -> bool:
    """
    Add a single vector to an existing index (or create a new one if none exists).
    """
    faiss = _faiss()
    if faiss is None:
        return False

    index_path, ids_path = _index_path(user_id)

    if index_path.exists():
        index = faiss.read_index(str(index_path))
        with open(ids_path) as f:
            ids = json.load(f)
    else:
        index = faiss.IndexFlatL2(EMBEDDING_DIM)
        ids = []

    index.add(vector.reshape(1, -1))
    ids.append(memory_id)

    faiss.write_index(index, str(index_path))
    with open(ids_path, "w") as f:
        json.dump(ids, f)
    return True


def search(user_id: str, query_vector: np.ndarray, top_k: int = 5) -> list[str]:
    """
    Search the user's index for top_k nearest memories.
    Returns list of memory UUIDs, closest first.
    Returns [] if index doesn't exist or FAISS unavailable.
    """
    faiss = _faiss()
    if faiss is None:
        return []

    index_path, ids_path = _index_path(user_id)
    if not index_path.exists():
        return []

    index = faiss.read_index(str(index_path))
    if index.ntotal == 0:
        return []

    k = min(top_k, index.ntotal)
    _distances, indices = index.search(query_vector.reshape(1, -1), k)

    with open(ids_path) as f:
        ids = json.load(f)

    return [ids[i] for i in indices[0] if 0 <= i < len(ids)]
