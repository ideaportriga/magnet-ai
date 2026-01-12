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

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from core.domain.knowledge_graph.service import KnowledgeGraphChunkService
from open_ai.utils_new import get_embeddings
from services.observability import observability_context, observe
from services.observability.models import SpanType

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


@observe(name="Find chunks by similarity", type=SpanType.SEARCH)
async def findChunksBySimilarity(
    db_session: AsyncSession,
    graph_id: UUID,
    q: str,
    embedding_model: str,
    *,
    limit: int,
    min_score: float,
    doc_filter_ids: list[str],
    doc_filter_where_sql: str | None = None,
    doc_filter_where_params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Return KG chunks most similar to the query embedding.

    This is used in the agentic ReAct loop as the "detail retrieval" step.

    Inputs:
    - **q / embedding_model**: used to produce the query embedding.
    - **limit / min_score**: hard filter after vector search.
    - **doc_filter_ids / doc_filter_where_sql**: optional restrictions computed
      by earlier tools (e.g., metadata filtering).

    Output:
    - A list of JSON-serializable chunk dicts (`ChunkSearchResult.to_json()`),
      filtered to `score >= min_score`.
    """
    observability_context.update_current_span(
        input={
            "query": q,
            "num_results": limit,
            "score_threshold": min_score,
        },
    )
    vec = await get_embeddings(q, embedding_model)
    chunks = await KnowledgeGraphChunkService().search_chunks(
        db_session,
        graph_id=graph_id,
        query_vector=vec,
        limit=limit,
        only_doc_ids=doc_filter_ids if doc_filter_ids else None,
        doc_filter_where_sql=doc_filter_where_sql,
        doc_filter_where_params=doc_filter_where_params,
    )
    observability_context.update_current_span(
        output=[c.to_json() for c in chunks],
    )
    return [c.to_json() for c in chunks if c.score is not None and c.score >= min_score]
