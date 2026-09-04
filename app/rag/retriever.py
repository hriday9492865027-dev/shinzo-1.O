"""
RAG — Retriever.

Manages a shared FAISS index for curated knowledge chunks and retrieves
relevant context for injection into the system prompt.

Unlike the per-user memory index, the RAG index is global (same for all users)
and is built from static documents in dataset/rag_docs/.

Usage:
    from app.rag.retriever import build_rag_index, retrieve_context
    build_rag_index("dataset/rag_docs/")   # call once at startup
    context = retrieve_context(query="feeling lonely after moving")
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from app.rag.chunking import chunk_directory
from app.rag.embeddings import EMBEDDING_DIM, embed, embed_batch

logger = logging.getLogger(__name__)

_RAG_INDEX_PATH = Path("shinzo_rag.index")
_RAG_CHUNKS_PATH = Path("shinzo_rag_chunks.json")

_chunks: list[dict] = []   # in-memory chunk store


def _faiss():
    try:
        import faiss  # type: ignore
        return faiss
    except ImportError:
        return None


def build_rag_index(docs_dir: str, glob: str = "*.txt") -> bool:
    """
    Build the RAG FAISS index from documents in docs_dir.
    Saves index and chunk metadata to disk.
    Returns True on success, False if FAISS unavailable or no documents found.
    """
    global _chunks
    faiss = _faiss()
    if faiss is None:
        logger.warning("FAISS not installed — RAG index unavailable.")
        return False

    all_chunks = chunk_directory(docs_dir, glob=glob)
    if not all_chunks:
        logger.info("No RAG documents found in %s — RAG disabled.", docs_dir)
        return False

    texts = [c["text"] for c in all_chunks]
    vectors = embed_batch(texts)

    index = faiss.IndexFlatL2(EMBEDDING_DIM)
    index.add(vectors)

    faiss.write_index(index, str(_RAG_INDEX_PATH))
    with open(_RAG_CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False)

    _chunks = all_chunks
    logger.info("Built RAG index: %d chunks from %s", len(all_chunks), docs_dir)
    return True


def load_rag_index() -> bool:
    """Load a previously-built RAG index from disk."""
    global _chunks
    faiss = _faiss()
    if faiss is None or not _RAG_INDEX_PATH.exists():
        return False
    if _RAG_CHUNKS_PATH.exists():
        with open(_RAG_CHUNKS_PATH, encoding="utf-8") as f:
            _chunks = json.load(f)
    return True


def retrieve_context(query: str, top_k: int = 3) -> str:
    """
    Retrieve top_k relevant chunks for `query`.
    Returns a formatted string for injection, or empty string if unavailable.
    """
    faiss = _faiss()
    if faiss is None or not _RAG_INDEX_PATH.exists() or not _chunks:
        return ""

    try:
        index = faiss.read_index(str(_RAG_INDEX_PATH))
        query_vec = embed(query).reshape(1, -1)
        k = min(top_k, index.ntotal)
        _, indices = index.search(query_vec, k)
        retrieved = [_chunks[i]["text"] for i in indices[0] if 0 <= i < len(_chunks)]
        if not retrieved:
            return ""
        lines = "\n".join(f"- {t}" for t in retrieved)
        return f"Relevant background context:\n{lines}"
    except Exception as exc:
        logger.error("RAG retrieval failed: %s", exc)
        return ""
