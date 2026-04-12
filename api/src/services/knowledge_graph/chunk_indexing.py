"""Chunk indexing utilities for knowledge graph content profiles.

Handles splitting chunk content into parts before embedding based on the
indexing settings from a content profile's chunker options.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Indexing mode values
INDEXING_MODE_WHOLE = "whole"
INDEXING_MODE_FIXED_PARTS = "fixed_parts"

# Overflow strategy values (used when mode is "whole")
OVERFLOW_STRATEGY_TRUNCATE = "truncate"
OVERFLOW_STRATEGY_SPLIT = "split"

# Defaults
DEFAULT_INDEXING_MODE = INDEXING_MODE_WHOLE
DEFAULT_OVERFLOW_STRATEGY = OVERFLOW_STRATEGY_TRUNCATE
DEFAULT_PART_SIZE = 500
DEFAULT_PART_OVERLAP = 0.0


def get_indexing_config(chunker_options: dict[str, Any] | None) -> dict[str, Any]:
    """Extract indexing settings from chunker options with defaults."""
    if not isinstance(chunker_options, dict):
        chunker_options = {}

    return {
        "indexing_mode": chunker_options.get("indexing_mode", DEFAULT_INDEXING_MODE),
        "indexing_overflow_strategy": chunker_options.get(
            "indexing_overflow_strategy", DEFAULT_OVERFLOW_STRATEGY
        ),
        "indexing_part_size": int(
            chunker_options.get("indexing_part_size", DEFAULT_PART_SIZE)
        ),
        "indexing_part_overlap": float(
            chunker_options.get("indexing_part_overlap", DEFAULT_PART_OVERLAP)
        ),
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
    chunk_max_size: int,
    indexing_config: dict[str, Any],
) -> list[str]:
    """Determine which text parts to embed for a single chunk.

    Args:
        embedded_content: The chunk text to embed.
        chunk_max_size: The configured chunk max size (characters).
        indexing_config: Output of :func:`get_indexing_config`.

    Returns:
        A list of text parts to embed individually. Each part will produce its
        own vector.  A single-element list means "embed the whole content as
        one vector" (the current default behaviour).
    """
    if not embedded_content:
        return []

    mode = indexing_config.get("indexing_mode", DEFAULT_INDEXING_MODE)
    part_size = int(indexing_config.get("indexing_part_size", DEFAULT_PART_SIZE))
    part_overlap = float(
        indexing_config.get("indexing_part_overlap", DEFAULT_PART_OVERLAP)
    )

    if mode == INDEXING_MODE_FIXED_PARTS:
        return split_text_into_parts(embedded_content, part_size, part_overlap)

    # mode == "whole" (default)
    overflow_strategy = indexing_config.get(
        "indexing_overflow_strategy", DEFAULT_OVERFLOW_STRATEGY
    )

    if chunk_max_size > 0 and len(embedded_content) > chunk_max_size:
        if overflow_strategy == OVERFLOW_STRATEGY_SPLIT:
            return split_text_into_parts(embedded_content, part_size, part_overlap)
        # truncate (default)
        return [embedded_content[:chunk_max_size]]

    return [embedded_content]
