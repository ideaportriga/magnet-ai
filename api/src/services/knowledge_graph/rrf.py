"""Reciprocal Rank Fusion and related helpers for hybrid retrieval.

RRF fuses multiple ranked result lists into a single ordering using

    score(d) = sum over ranked lists L: 1 / (k + rank_L(d))

where ``rank_L(d)`` is the 1-based position of ``d`` in list ``L`` (items
absent from ``L`` contribute nothing). The constant ``k`` dampens the
contribution of lower-ranked items; the canonical default is 60.

The module is domain-agnostic — it operates on lists of any hashable
identifier — so it can fuse results from any combination of retrieval
strategies (pgvector, tsvector, BM25, external search APIs, …).

Note: a domain-specific RRF implementation also lives in
:mod:`utils.search_utils` for use by the Oracle vector store; that one is
coupled to ``DocumentSearchResult`` and is not interchangeable with this
generic one.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Any, Hashable, Iterable, TypeVar

from sqlalchemy import text

from services.observability import observability_context, observe
from services.observability.models import SpanType

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=Hashable)


def reciprocal_rank_fusion(
    rank_lists: Iterable[Iterable[T]],
    *,
    k: int = 60,
) -> list[tuple[T, float]]:
    """Fuse ranked lists of IDs into a single ``(id, rrf_score)`` list.

    The result is sorted by score descending. Items appearing in multiple
    lists are deduplicated and their scores summed. ``k`` must be >= 1.
    """

    if k < 1:
        k = 1

    scores: dict[T, float] = defaultdict(float)
    for rank_list in rank_lists:
        for rank, item in enumerate(rank_list, start=1):
            scores[item] += 1.0 / (k + rank)

    return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)


def merge_attempts_by_max_score(
    attempts: Iterable[Iterable[tuple[T, float]]],
) -> list[T]:
    """Collapse multiple ``(id, score)`` lists from one method into one ranking.

    Each input list is the result of a single query-variant *attempt* of the
    **same** search method (e.g. several reformulated keyword queries all run
    through full-text search). Because they share a scoring scale, we keep the
    best (max) score per id and return ids sorted by score descending. This is
    the merge-and-dedup step that runs *before* cross-method RRF, so attempts of
    one method count as a single voter rather than fusing independently.
    """

    best: dict[T, float] = {}
    for attempt in attempts:
        for item, score in attempt:
            if item not in best or score > best[item]:
                best[item] = score
    return [
        item for item, _ in sorted(best.items(), key=lambda kv: kv[1], reverse=True)
    ]


def normalized_rrf_score(raw_score: float, *, num_methods: int, k: int = 60) -> float:
    """Normalize an RRF score to [0, 1] using the theoretical max.

    The maximum possible RRF score for an item that ranks #1 in every
    contributing list is ``num_methods * 1/(k+1)``. We divide by that so
    downstream knobs (e.g. ``scoreThreshold``) remain bounded in [0, 1].
    """

    if num_methods <= 0:
        return 0.0
    max_score = num_methods * (1.0 / (max(k, 1) + 1))
    if max_score <= 0:
        return 0.0
    return max(0.0, min(1.0, raw_score / max_score))


async def _execute_hybrid_subquery(
    method: str,
    query: str,
    sql: str,
    params: dict[str, Any],
    session_maker: Any,
    pre_statements: list[str] | None = None,
) -> list[tuple[str, float]]:
    """Run a candidate sub-query and return ``(id, score)`` rows in rank order.

    The sub-query must ``SELECT id, score`` (score is the method's own relevance
    measure: cosine similarity or ts_rank_cd). ``pre_statements`` are executed in
    the same session/transaction before the main query (e.g. a ``SET LOCAL`` to
    tune a session GUC).
    """

    started = time.perf_counter()
    try:
        async with session_maker() as session:
            for stmt in pre_statements or []:
                await session.execute(text(stmt))
            rows = (await session.execute(text(sql), params)).all()
    except Exception:
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        observability_context.update_current_span(input={"query": query})
        logger.exception(
            "hybrid sub-query failed method=%s elapsed_ms=%.2f", method, elapsed_ms
        )
        raise

    results = [
        (str(r[0]), float(r[1]) if r[1] is not None else 0.0)
        for r in rows
        if r[0] is not None
    ]
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    observability_context.update_current_span(
        input={"query": query}, output={"count": len(results)}
    )
    logger.info(
        "hybrid sub-query method=%s results=%d elapsed_ms=%.2f",
        method,
        len(results),
        elapsed_ms,
    )
    return results


@observe(
    name="Vector search",
    type=SpanType.SEARCH,
    description="pgvector cosine-similarity search over content/summary embeddings.",
)
async def hybrid_vector_search(
    query: str,
    sql: str,
    params: dict[str, Any],
    *,
    session_maker: Any,
) -> list[tuple[str, float]]:
    """Parallel hybrid sub-query: pgvector cosine similarity over embeddings."""
    return await _execute_hybrid_subquery("vector", query, sql, params, session_maker)


@observe(
    name="Full-text search",
    type=SpanType.SEARCH,
    description="Postgres full-text search (tsvector / plainto_tsquery) over lexical tokens.",
)
async def hybrid_full_text_search(
    query: str,
    sql: str,
    params: dict[str, Any],
    *,
    session_maker: Any,
) -> list[tuple[str, float]]:
    """Parallel hybrid sub-query: Postgres full-text search via ``tsvector``."""
    return await _execute_hybrid_subquery(
        "full_text", query, sql, params, session_maker
    )


def fusion_diagnostics(
    *,
    method_results: dict[str, list[T]],
    fused: list[tuple[T, float]],
    num_methods: int,
    k: int,
) -> dict[str, Any]:
    """Build a diagnostics dict for trace/log enrichment after RRF.

    Returns counts per method, unique candidate count, multi-method overlap,
    and the top normalized score so observability spans can record what
    actually happened during fusion.
    """

    per_method_counts = {m: len(ids) for m, ids in method_results.items()}
    unique_ids: set[T] = set()
    for ids in method_results.values():
        unique_ids.update(ids)
    overlap = 0
    if len(method_results) >= 2:
        for cid in unique_ids:
            seen = sum(1 for ids in method_results.values() if cid in ids)
            if seen >= 2:
                overlap += 1
    top_raw = fused[0][1] if fused else 0.0
    top_normalized = normalized_rrf_score(top_raw, num_methods=num_methods, k=k)
    return {
        "per_method_result_count": per_method_counts,
        "unique_candidates": len(unique_ids),
        "multi_method_overlap": overlap,
        "fused_total": len(fused),
        "top_rrf_score_raw": round(top_raw, 6),
        "top_rrf_score_normalized": round(top_normalized, 6),
    }


def vector_literal(values: list[float]) -> str:
    """Format a list of floats as a pgvector text literal: ``[1.0,2.0,...]``.

    Useful when binding a query vector through raw SQL (e.g.
    ``CAST(:qvec AS vector)``) without relying on driver-level codec
    registration.
    """
    return "[" + ",".join(repr(float(v)) for v in values) + "]"
