"""
Semantic memory retrieval — returns the most relevant memories for a given query.

Usage (called from context_builder.py):
    from app.memory.retrieval import get_relevant_memories
    memories = get_relevant_memories(user_id="u1", query="my job interview")
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime

from app.memory.db import get_session
from app.memory.embeddings import embed
from app.memory.index import search
from app.memory.models import Memory

logger = logging.getLogger(__name__)

DEFAULT_TOP_K = 5
MIN_IMPORTANCE_FILTER = 0.35  # skip very low-importance memories at retrieval time


def get_relevant_memories(
    user_id: str,
    query: str,
    top_k: int = DEFAULT_TOP_K,
) -> list[str]:
    """
    Retrieve top_k most semantically relevant memories for `query`.
    Returns a list of memory content strings, sorted by relevance.
    Returns [] if no memories exist or FAISS is unavailable.
    """
    query_vector = embed(query)
    memory_ids = search(user_id=user_id, query_vector=query_vector, top_k=top_k)

    if not memory_ids:
        return []

    with get_session() as session:
        memories = (
            session.query(Memory)
            .filter(Memory.id.in_(memory_ids), Memory.importance >= MIN_IMPORTANCE_FILTER)
            .all()
        )
        # Update last_accessed_at timestamps
        now = datetime.now(UTC)
        for mem in memories:
            mem.last_accessed_at = now

        # Sort by the FAISS result order (closest first)
        id_order = {mid: idx for idx, mid in enumerate(memory_ids)}
        memories.sort(key=lambda m: id_order.get(m.id, 999))

        contents = [m.content for m in memories]

    logger.debug("Retrieved %d memories for user %s", len(contents), user_id)
    return contents


def format_memories_for_context(memories: list[str]) -> str:
    """
    Format a list of memory strings for injection into a system prompt.
    Returns empty string if no memories.
    """
    if not memories:
        return ""
    bullet_list = "\n".join(f"- {m}" for m in memories)
    return f"Things I remember about you:\n{bullet_list}"
