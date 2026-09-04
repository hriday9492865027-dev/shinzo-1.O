"""
RAG — Document chunking.

Splits curated knowledge documents into retrievable chunks.
Documents live in dataset/rag_docs/ (plain text or markdown files).
"""
from __future__ import annotations

import re
from pathlib import Path

DEFAULT_CHUNK_SIZE = 400    # characters
DEFAULT_CHUNK_OVERLAP = 80  # characters


def chunk_text(text: str, chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_CHUNK_OVERLAP) -> list[str]:
    """
    Split text into overlapping chunks of roughly `chunk_size` characters.
    Tries to split on sentence boundaries first.
    """
    # Split on sentence endings
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        if len(current) + len(sentence) <= chunk_size:
            current = (current + " " + sentence).strip()
        else:
            if current:
                chunks.append(current)
            # Start new chunk with overlap from end of previous
            overlap_text = current[-overlap:] if len(current) > overlap else current
            current = (overlap_text + " " + sentence).strip()

    if current:
        chunks.append(current)

    return [c for c in chunks if len(c.strip()) > 20]


def chunk_file(path: str | Path, **kwargs) -> list[dict]:
    """
    Read a file and return chunked records: [{"text": "...", "source": "filename"}]
    """
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    chunks = chunk_text(text, **kwargs)
    return [{"text": c, "source": path.name} for c in chunks]


def chunk_directory(directory: str | Path, glob: str = "*.txt", **kwargs) -> list[dict]:
    """
    Chunk all matching files in a directory.
    """
    all_chunks = []
    for p in Path(directory).glob(glob):
        all_chunks.extend(chunk_file(p, **kwargs))
    return all_chunks
