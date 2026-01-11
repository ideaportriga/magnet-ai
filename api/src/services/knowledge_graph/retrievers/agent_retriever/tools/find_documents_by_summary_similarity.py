"""
Knowledge Graph retrieval tool: `findDocumentsBySummarySimilarity`.

This is the "coarse" retrieval step used by the agentic loop to find relevant
documents before doing chunk-level retrieval.

As with other tools in this package:
- **TOOL_SPEC** defines the OpenAI tool schema sent to the LLM.
- **findDocumentsBySummarySimilarity(...)** is the implementation.
"""

from typing import Any, NamedTuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from core.domain.knowledge_graph.service import KnowledgeGraphDocumentService
from open_ai.utils_new import get_embeddings
from services.observability import observability_context, observe
from services.observability.models import SpanType

from ....models import KnowledgeGraphRetrievalWorkflowStep

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


@observe(name="Find documents by summary similarity", type=SpanType.SEARCH)
async def findDocumentsBySummarySimilarity(
    db_session: AsyncSession,
    graph_id: UUID,
    *,
    query: str,
    embedding_model: str,
    args: dict[str, Any],
    iteration: int,
    tool_name: str = "findDocumentsBySummarySimilarity",
    tool_cfg: dict[str, Any] | None = None,
) -> FindDocumentsBySummarySimilarityToolResult:
    """
    Agent tool execution for `findDocumentsBySummarySimilarity`.

    Returns a 3-tuple consumed by the agent loop:
    1) Tool payload for the LLM (count only; never the documents)
    2) Loop state updates (document IDs for later chunk retrieval filtering)
    3) Workflow step for the API response

    The effective search knobs are determined by graph config:
    - searchControl: "agent" lets the model control limit/scoreThreshold
    - otherwise, limit/scoreThreshold come from the graph settings (tool_cfg)
    """

    args = args if isinstance(args, dict) else {}
    tool_cfg_d = tool_cfg if isinstance(tool_cfg, dict) else {}

    # Graph-configured defaults
    configured_limit = int(tool_cfg_d.get("limit", 5))
    configured_threshold = float(tool_cfg_d.get("scoreThreshold", 0.7))

    search_control = str(tool_cfg_d.get("searchControl") or "").strip().lower()
    if search_control == "agent":
        # Let the model control knobs (with sane fallbacks to config)
        limit = int(args.get("limit", configured_limit))
        min_score = float(args.get("scoreThreshold", configured_threshold))
    else:
        limit = configured_limit
        min_score = configured_threshold

    if limit <= 0:
        limit = configured_limit if configured_limit > 0 else 1

    observability_context.update_current_span(
        input={
            "query": query,
            "num_results": limit,
            "score_threshold": min_score,
        },
    )

    vec = await get_embeddings(query, embedding_model)
    docs = await KnowledgeGraphDocumentService().search_documents(
        db_session,
        graph_id=graph_id,
        query_vector=vec,
        limit=limit,
    )
    filtered_docs = [d for d in docs if d.get("score", 0.0) >= min_score]
    doc_ids = [str(d.get("id")) for d in filtered_docs if d.get("id")]
    count = len(doc_ids)

    observability_context.update_current_span(
        output={
            "count": count,
            "document_ids": doc_ids,
        },
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
