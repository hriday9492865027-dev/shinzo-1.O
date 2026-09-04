"""
Shared Context — injects shared references and callbacks naturally.

When there are relevant memories or prior conversation moments, this module
decides whether and how to surface them in the context. The goal is the
feeling of a friend who remembers — not a system that announces its memory.
"""
from __future__ import annotations


def build_context_note(memories: list[str], dynamics_depth: float) -> str:
    """
    If memories are present, format them for injection. Only surface when depth
    makes it feel natural — don't force callbacks into surface chat.
    """
    if not memories:
        return ""

    # In casual/surface conversations, callbacks feel performative — skip them
    if dynamics_depth < 0.20:
        return ""

    # Pick the top 2–3 most relevant (already ranked by retrieval.py)
    selected = memories[:3]
    lines = "\n".join(f"- {m}" for m in selected)
    return (
        "Relevant things from our past conversations "
        "(weave these in only if they fit naturally — don't announce you remembered them):\n"
        + lines
    )
