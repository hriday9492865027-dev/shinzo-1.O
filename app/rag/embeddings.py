"""
RAG — Chunk embeddings.

Reuses app/memory/embeddings.py pattern but namespaced for RAG documents.
The separation keeps memory (personal, per-user) distinct from RAG (curated knowledge, shared).
"""
from __future__ import annotations

# Re-export from the shared embeddings utility — RAG uses the same model
from app.memory.embeddings import EMBEDDING_DIM, embed, embed_batch

__all__ = ["embed", "embed_batch", "EMBEDDING_DIM"]
