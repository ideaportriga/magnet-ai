"""
Knowledge Graph retrieval tool: `findDocumentsBySummarySimilarity`.

This is the "coarse" retrieval step used by the agentic loop to find relevant
documents before doing chunk-level retrieval.

As with other tools in this package:
- **TOOL_SPEC** defines the OpenAI tool schema sent to the LLM.
- **findDocumentsBySummarySimilarity(...)** is the implementation.
"""

import logging
import time
from typing import Any, NamedTuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from core.domain.knowledge_graph.services import KnowledgeGraphDocumentService
from open_ai.utils_new import get_embeddings
from services.observability import observability_context, observe
from services.observability.models import SpanType

from ....models import KnowledgeGraphRetrievalWorkflowStep

logger = logging.getLogger(__name__)

# OpenAI tool schema (sent to the LLM).
# `get_available_tools()` may augment this schema at runtime based on graph config.
TOOL_SPEC: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "findDocumentsBySummarySimilarity",
        "description": "Find documents by summary similarity",
        "parameters": {
            "type": "object",
            "properties": {
                "reasoning": {
                    "type": "string",
                    "description": (
                        "Why you are using this tool (e.g., "
                        "'Locating manuals related to hydraulic pumps')."
                    ),
                },
                "query": {
                    "type": "string",
                    "description": (
                        "The search query. The system will automatically create an "
                        "embedding from this."
                    ),
                },
            },
            "required": ["query", "reasoning"],
        },
    },
}


class FindDocumentsBySummarySimilarityToolResult(NamedTuple):
    """
    Result contract for `findDocumentsBySummarySimilarity` used by the retrieval agent loop.

    1) tool_payload: JSON-serializable content to send back to the LLM as the tool result
    2) loop_state: internal state the agent loop should keep for subsequent tool calls
    3) workflow_step: `KnowledgeGraphRetrievalWorkflowStep` to append to `workflow_steps`
    """

    tool_payload: dict[str, Any]
    loop_state: dict[str, Any]
    workflow_step: KnowledgeGraphRetrievalWorkflowStep


@observe(
    name="Find documents by summary similarity",
    type=SpanType.TOOL,
    description=(
        "Knowledge-graph retrieval tool: returns documents whose summary best matches "
        "the query using the graph's configured search method (vector / keyword / hybrid)."
    ),
)
async def findDocumentsBySummarySimilarity(
    db_session: AsyncSession,
    graph_id: UUID,
    *,
    query: str,
    embedding_model: str,
    args: dict[str, Any],
    iteration: int,
    tool_cfg: dict[str, Any],
    tool_name: str = "findDocumentsBySummarySimilarity",
) -> FindDocumentsBySummarySimilarityToolResult:
    """
    Agent tool execution for `findDocumentsBySummarySimilarity`.

    Returns a 3-tuple consumed by the agent loop:
    1) Tool payload for the LLM (count only; never the documents)
    2) Loop state updates (document IDs for later chunk retrieval filtering)
    3) Workflow step for the API response

    The effective search knobs (limit/scoreThreshold) come from the graph settings (tool_cfg).
    """

    limit = int(tool_cfg["limit"])
    min_score = float(tool_cfg["scoreThreshold"])

    search_method = tool_cfg["searchMethod"]
    rrf_k = int(tool_cfg["rrfK"])

    logger.info(
        "findDocumentsBySummarySimilarity start iteration=%d graph_id=%s method=%s "
        "limit=%d threshold=%.3f rrf_k=%d query=%r",
        iteration,
        graph_id,
        search_method,
        limit,
        min_score,
        rrf_k,
        query[:120],
    )

    observability_context.update_current_span(
        input={
            "query": query,
            "num_results": limit,
            "score_threshold": min_score,
            "search_method": search_method,
            "rrf_k": rrf_k,
            "iteration": iteration,
        },
        extra_data={"tool_type": "search"},
    )

    # Embedding is only needed for vector and hybrid modes.
    started = time.perf_counter()
    embedding_ms: float | None = None
    if search_method in ("keyword", "full_text"):
        vec: list[float] | None = None
    else:
        embed_started = time.perf_counter()
        vec = await get_embeddings(query, embedding_model)
        embedding_ms = round((time.perf_counter() - embed_started) * 1000, 2)

    docs = await KnowledgeGraphDocumentService().search_documents(
        db_session,
        graph_id=graph_id,
        search_method=search_method,
        query_vector=vec,
        query_text=query,
        rrf_k=rrf_k,
        limit=limit,
    )
    filtered_docs = [d for d in docs if d.get("score", 0.0) >= min_score]
    doc_ids = [str(d.get("id")) for d in filtered_docs if d.get("id")]
    count = len(doc_ids)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    top_scores = [round(float(d.get("score") or 0.0), 4) for d in filtered_docs[:5]]
    dropped_by_threshold = len(docs) - count

    # Keep the parent span's `output` minimal (matching the original shape)
    # so the trace UI shows the same information it has always shown.
    # Detailed hybrid statistics live in `extra_data`.
    observability_context.update_current_span(
        output={
            "count": count,
            "document_ids": doc_ids,
        }
    )
    logger.info(
        "findDocumentsBySummarySimilarity done iteration=%d method=%s raw=%d kept=%d "
        "dropped=%d embedding_ms=%s total_ms=%.2f top_scores=%s",
        iteration,
        search_method,
        len(docs),
        count,
        dropped_by_threshold,
        embedding_ms,
        elapsed_ms,
        top_scores,
    )

    tool_payload = {"matched_documents": count}
    loop_state = {"doc_filter_ids": doc_ids}
    workflow_step = KnowledgeGraphRetrievalWorkflowStep(
        iteration=iteration,
        tool=tool_name,
        arguments={"query": query},
        call_summary={
            "reasoning": args.get("reasoning"),
            "result_count": count,
        },
    )

    return FindDocumentsBySummarySimilarityToolResult(
        tool_payload=tool_payload,
        loop_state=loop_state,
        workflow_step=workflow_step,
    )
