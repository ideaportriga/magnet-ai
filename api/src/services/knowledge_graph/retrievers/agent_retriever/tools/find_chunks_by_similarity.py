"""
Knowledge Graph retrieval tool: `findChunksBySimilarity`.

This module contains two closely-related pieces:

1) **TOOL_SPEC**: the OpenAI "function tool" schema that is sent to the LLM.
2) **findChunksBySimilarity(...)**: the actual server-side implementation.

Keeping the schema next to the implementation makes it easy to evolve the tool
contract without hunting through a central registry file.

Note: The tool spec uses argument names like `query` / `scoreThreshold`, while the
implementation uses `q` / `min_score`. The mapping is performed by the retrieval
agent loop (`agent.py`), not here.
"""

import logging
import time
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from core.domain.knowledge_graph.services import KnowledgeGraphChunkService
from open_ai.utils_new import get_embeddings
from services.observability import observability_context, observe
from services.observability.models import SpanType

logger = logging.getLogger(__name__)

# OpenAI tool schema (sent to the LLM).
# `get_available_tools()` may augment this schema at runtime based on graph config.
TOOL_SPEC: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "findChunksBySimilarity",
        "description": "Find chunks by similarity",
        "parameters": {
            "type": "object",
            "properties": {
                "reasoning": {
                    "type": "string",
                    "description": "Why you are using this tool.",
                },
                "query": {
                    "type": "string",
                    "description": (
                        "The specific search query for details. "
                        "The system will automatically create an embedding from this."
                    ),
                },
            },
            "required": ["query", "reasoning"],
        },
    },
}


@observe(
    name="Find chunks by similarity",
    type=SpanType.TOOL,
    description=(
        "Knowledge-graph retrieval tool: returns chunks most similar to the query "
        "using the graph's configured search method (vector / keyword / hybrid)."
    ),
)
async def findChunksBySimilarity(
    db_session: AsyncSession,
    graph_id: UUID,
    q: str,
    embedding_model: str,
    *,
    limit: int,
    min_score: float,
    doc_filter_ids: list[str],
    tool_cfg: dict[str, Any],
    doc_filter_where_sql: str | None = None,
    doc_filter_where_params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Return KG chunks most similar to the query embedding.

    This is used in the agentic ReAct loop as the "detail retrieval" step.

    Inputs:
    - **q / embedding_model**: used to produce the query embedding.
    - **limit / min_score**: hard filter after retrieval.
    - **doc_filter_ids / doc_filter_where_sql**: optional restrictions computed
      by earlier tools (e.g., metadata filtering).
    - **tool_cfg**: graph-configured tool settings; supplies ``searchMethod``
      (``vector`` | ``keyword`` | ``hybrid``) and ``rrfK`` (RRF constant).

    Output:
    - A list of JSON-serializable chunk dicts (`ChunkSearchResult.to_json()`),
      filtered to `score >= min_score`.
    """

    search_method = tool_cfg["searchMethod"]
    rrf_k = int(tool_cfg["rrfK"])
    doc_filter_count = len(doc_filter_ids) if doc_filter_ids else 0

    logger.info(
        "findChunksBySimilarity start graph_id=%s method=%s limit=%d threshold=%.3f "
        "rrf_k=%d doc_filter_ids=%d query=%r",
        graph_id,
        search_method,
        limit,
        min_score,
        rrf_k,
        doc_filter_count,
        q[:120],
    )

    observability_context.update_current_span(
        input={
            "query": q,
            "num_results": limit,
            "score_threshold": min_score,
            "search_method": search_method,
            "rrf_k": rrf_k,
            "doc_filter_ids_count": doc_filter_count,
            "metadata_filter_active": bool(doc_filter_where_sql),
        },
        extra_data={"tool_type": "search"},
    )

    started = time.perf_counter()
    embedding_ms: float | None = None
    if search_method == "keyword":
        vec: list[float] | None = None
    else:
        embed_started = time.perf_counter()
        vec = await get_embeddings(q, embedding_model)
        embedding_ms = round((time.perf_counter() - embed_started) * 1000, 2)

    chunks = await KnowledgeGraphChunkService().search_chunks(
        db_session,
        graph_id=graph_id,
        search_method=search_method,
        query_vector=vec,
        query_text=q,
        rrf_k=rrf_k,
        limit=limit,
        only_doc_ids=doc_filter_ids if doc_filter_ids else None,
        doc_filter_where_sql=doc_filter_where_sql,
        doc_filter_where_params=doc_filter_where_params,
    )

    kept = [c for c in chunks if c.score is not None and c.score >= min_score]
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    top_scores = [round(float(c.score or 0.0), 4) for c in kept[:5]]
    dropped_by_threshold = len(chunks) - len(kept)

    # Keep the parent span's `output` as the actual retrieved chunks — that's
    # what humans want to see when they open the trace. Hybrid statistics
    # live separately in `extra_data` so they don't crowd the output panel.
    observability_context.update_current_span(output=[c.to_json() for c in kept])
    logger.info(
        "findChunksBySimilarity done method=%s raw=%d kept=%d dropped=%d "
        "embedding_ms=%s total_ms=%.2f top_scores=%s",
        search_method,
        len(chunks),
        len(kept),
        dropped_by_threshold,
        embedding_ms,
        elapsed_ms,
        top_scores,
    )
    return [c.to_json() for c in kept]
