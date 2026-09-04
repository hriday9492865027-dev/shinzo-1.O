"""
Memory write path — stores approved memory candidates to the DB and updates the FAISS index.

Usage (called from the orchestrator after each turn):
    from app.memory.store import save_turn_memories
    save_turn_memories(user_id=..., conversation_id=..., user_message=...)
"""
from __future__ import annotations

import json
import logging

from app.memory.db import get_session
from app.memory.embeddings import embed
from app.memory.extraction import extract
from app.memory.importance_scoring import filter_candidates
from app.memory.index import add_to_index
from app.memory.models import Memory

logger = logging.getLogger(__name__)


def store_memory(
    user_id: str,
    content: str,
    importance: float,
    source_conversation_id: str | None = None,
) -> str:
    """
    Persist a single memory to the DB and add its embedding to the FAISS index.
    Returns the new memory's UUID.
    """
    vector = embed(content)
    vector_json = json.dumps(vector.tolist())

    with get_session() as session:
        mem = Memory(
            user_id=user_id,
            content=content,
            importance=importance,
            source_conversation_id=source_conversation_id,
            embedding_json=vector_json,
        )
        session.add(mem)
        session.flush()  # get the generated ID before commit
        memory_id = mem.id

    add_to_index(user_id, vector, memory_id)
    logger.debug("Stored memory %s for user %s (importance=%.2f)", memory_id, user_id, importance)
    return memory_id


def save_turn_memories(
    user_id: str,
    user_message: str,
    conversation_id: str | None = None,
) -> list[str]:
    """
    Full pipeline: extract → score → filter → store.
    Called once per conversation turn.
    Returns list of stored memory UUIDs (empty if nothing was worth storing).
    """
    candidates = extract(user_message)
    if not candidates:
        return []

    approved = filter_candidates(candidates)
    stored_ids = []
    for content, importance in approved:
        mid = store_memory(
            user_id=user_id,
            content=content,
            importance=importance,
            source_conversation_id=conversation_id,
        )
        stored_ids.append(mid)

    return stored_ids
