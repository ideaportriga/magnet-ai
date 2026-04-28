"""Chunk indexing utilities for knowledge graph content profiles.

Splits chunk content into parts before embedding when it exceeds the
configured ``embedding_max_size``; otherwise embeds the chunk as a single
vector.
"""

from __future__ import annotations

import logging
import math
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


def split_text_into_parts(
    text: str, embedding_max_size: int, overlap: float = 0.0
) -> list[str]:
    """Split text into equal-sized parts, each at most ``embedding_max_size`` characters.

    Computes the minimum number of parts N required to cover the full text such
    that every part fits within ``embedding_max_size``. All N parts have identical
    length. Parts are positioned using a floating-point step to distribute rounding
    evenly, with the final part anchored to the end of the text to guarantee exact
    coverage.

    Args:
        text: The text to split.
        embedding_max_size: Maximum characters per part (upper bound).
        overlap: Desired overlap ratio between consecutive parts (0.0–0.9).

    Returns:
        List of equal-length text segments. Returns a single-element list when
        ``len(text) <= embedding_max_size`` or ``embedding_max_size <= 0``.
        Returns ``[]`` for empty text.
    """
    if not text:
        return []

    if embedding_max_size <= 0:
        return [text]

    text_len = len(text)
    overlap = max(0.0, min(overlap, 0.9))

    if text_len <= embedding_max_size:
        return [text]

    # Minimum N so every part stays within embedding_max_size
    step_max = max(1, embedding_max_size * (1.0 - overlap))
    n = math.ceil((text_len - embedding_max_size) / step_max) + 1  # n >= 2

    # Equal part size P such that P * (1 + (n-1) * (1-overlap)) >= text_len
    # Guaranteed P <= embedding_max_size by construction of n
    denom = 1.0 + (n - 1) * (1.0 - overlap)
    p = math.ceil(text_len / denom)

    # Float step distributes rounding error evenly; anchor last start to avoid end gap
    float_step = (text_len - p) / (n - 1)
    starts = [round(i * float_step) for i in range(n)]
    starts[-1] = text_len - p

    return [text[s : s + p] for s in starts]


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
