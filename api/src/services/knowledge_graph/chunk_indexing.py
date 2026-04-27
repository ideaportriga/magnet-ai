"""Chunk indexing utilities for knowledge graph content profiles.

Splits chunk content into parts before embedding when it exceeds the
configured ``embedding_max_size``; otherwise embeds the chunk as a single
vector.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_PART_OVERLAP = 0.0
DEFAULT_EMBEDDING_MAX_SIZE = 18000


def get_indexing_config(chunker_options: dict[str, Any] | None) -> dict[str, Any]:
    """Extract indexing settings from chunker options with defaults.

    ``embedding_max_size`` is the per-embedding-call cap. Falls back to the
    legacy ``chunk_max_size`` key when reading older profiles, so either the
    backend or frontend deploy can land first.
    """
    if not isinstance(chunker_options, dict):
        chunker_options = {}

    embedding_max_size_raw = chunker_options.get("embedding_max_size")
    if embedding_max_size_raw is None:
        embedding_max_size_raw = chunker_options.get("chunk_max_size")
    try:
        embedding_max_size = (
            int(embedding_max_size_raw)
            if embedding_max_size_raw is not None
            else DEFAULT_EMBEDDING_MAX_SIZE
        )
    except (TypeError, ValueError):
        embedding_max_size = DEFAULT_EMBEDDING_MAX_SIZE

    return {
        "indexing_part_overlap": float(
            chunker_options.get("indexing_part_overlap", DEFAULT_PART_OVERLAP)
        ),
        "embedding_max_size": embedding_max_size,
    }


def split_text_into_parts(text: str, part_size: int, overlap: float = 0.0) -> list[str]:
    """Split text into fixed-size parts with overlap.

    Args:
        text: The text to split.
        part_size: Maximum number of characters per part.
        overlap: Overlap ratio between consecutive parts (0.0–0.9).

    Returns:
        List of text segments. Always returns at least one part if text is
        non-empty.
    """
    if not text:
        return []

    if part_size <= 0:
        return [text]

    overlap = max(0.0, min(overlap, 0.9))
    overlap_chars = int(part_size * overlap)
    step = max(1, part_size - overlap_chars)

    parts: list[str] = []
    pos = 0
    text_len = len(text)

    while pos < text_len:
        end = pos + part_size
        parts.append(text[pos:end])
        if end >= text_len:
            break
        pos += step

    return parts


def prepare_embedding_parts(
    embedded_content: str,
    indexing_config: dict[str, Any],
) -> list[str]:
    """Determine which text parts to embed for a single chunk.

    Args:
        embedded_content: The chunk text to embed.
        indexing_config: Output of :func:`get_indexing_config` (carries
            ``embedding_max_size`` and ``indexing_part_overlap``).

    Returns:
        A list of text parts to embed individually. Each part will produce its
        own vector. A single-element list means "embed the whole content as
        one vector".
    """
    if not embedded_content:
        return []

    part_overlap = float(
        indexing_config.get("indexing_part_overlap", DEFAULT_PART_OVERLAP)
    )
    embedding_max_size = int(
        indexing_config.get("embedding_max_size", DEFAULT_EMBEDDING_MAX_SIZE)
    )

    if embedding_max_size > 0 and len(embedded_content) > embedding_max_size:
        return split_text_into_parts(embedded_content, embedding_max_size, part_overlap)

    return [embedded_content]
