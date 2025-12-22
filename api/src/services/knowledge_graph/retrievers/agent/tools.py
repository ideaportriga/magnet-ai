import copy
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from core.domain.knowledge_graph.schemas import ChunkSearchResult
from core.domain.knowledge_graph.service import KnowledgeGraphChunkService
from open_ai.utils_new import get_embeddings
from services.knowledge_graph.store_services import search_documents
from services.observability import (
    observability_context,
    observability_overrides,
    observe,
)
from services.observability.models import SpanType


@observe(name="Find documents by summary similarity", type=SpanType.SEARCH)
async def findDocumentsBySummarySimilarity(
    graph_id: UUID,
    q: str,
    embedding_model: str,
    *,
    limit: int,
    min_score: float,
) -> list[dict[str, Any]]:
    observability_context.update_current_span(
        input={
            "query": q,
            "num_results": limit,
            "score_threshold": min_score,
        },
    )
    vec = await get_embeddings(q, embedding_model)
    docs = await search_documents(graph_id, vec, limit)
    observability_context.update_current_span(
        output=docs,
    )
    return [d for d in docs if d.get("score", 0.0) >= min_score]


@observe(name="Find chunks by similarity", type=SpanType.SEARCH)
async def findChunksBySimilarity(
    db_session: AsyncSession,
    graph_id: UUID,
    q: str,
    embedding_model: str,
    *,
    limit: int,
    min_score: float,
    # TODO: figure out how to pass document query to filter chunks
    doc_filter_ids: list[str],
) -> list[ChunkSearchResult]:
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
    )
    observability_context.update_current_span(
        output=[c.to_json() for c in chunks],
    )
    return [c.to_json() for c in chunks if c.score is not None and c.score >= min_score]


RETRIEVAL_AGENT_TOOLS = {
    "findDocumentsBySummarySimilarity": {
        "tool_spec": {
            "type": "function",
            "function": {
                "name": "findDocumentsBySummarySimilarity",
                "description": "Find documents by summary similarity",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reasoning": {
                            "type": "string",
                            "description": "Why you are using this tool (e.g., 'Locating manuals related to hydraulic pumps').",
                        },
                        "query": {
                            "type": "string",
                            "description": "The search query. The system will automatically create an embedding from this.",
                        },
                    },
                    "required": ["query", "reasoning"],
                },
            },
        },
        "tool_impl": findDocumentsBySummarySimilarity,
    },
    "findChunksBySimilarity": {
        "tool_spec": {
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
                            "description": "The specific search query for details. The system will automatically create an embedding from this.",
                        },
                    },
                    "required": ["query", "reasoning"],
                },
            },
        },
        "tool_impl": findChunksBySimilarity,
    },
    "exit": {
        "tool_spec": {
            "type": "function",
            "function": {
                "name": "exit",
                "description": "Exit the tool call loop",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reasoning": {
                            "type": "string",
                            "description": "Confidence assessment and why you are ready to answer.",
                        },
                        "answer": {
                            "type": "string",
                            "description": "The complete final answer with citations. Format: Blockquote with source, followed by .",
                        },
                    },
                    "required": ["reasoning", "answer"],
                },
            },
        },
    },
}


def get_available_tools(retrieval_tools_cfg: dict[str, Any]) -> list[dict[str, Any]]:
    available_tools: list[dict[str, Any]] = []
    for tool_name, tool_cfg in retrieval_tools_cfg.items():
        if tool_name not in RETRIEVAL_AGENT_TOOLS:
            continue

        if not tool_cfg.get("enabled", True):
            continue

        original_tool = copy.deepcopy(RETRIEVAL_AGENT_TOOLS[tool_name]["tool_spec"])

        # Override description if provided in config
        if description := tool_cfg.get("description"):
            original_tool["function"]["description"] = description

        # If searchControl is agent, add limit and scoreThreshold to parameters
        if tool_cfg.get("searchControl") == "agent":
            parameters = original_tool["function"]["parameters"]
            parameters["properties"]["limit"] = {
                "type": "integer",
                "description": "The maximum number of results to return.",
            }
            parameters["properties"]["scoreThreshold"] = {
                "type": "number",
                "description": "The minimum similarity score (0.0 to 1.0) for the results.",
            }
            parameters["required"].extend(["limit", "scoreThreshold"])

        available_tools.append(original_tool)

    # Ensure exit tool is always available if not explicitly disabled or missing (though typically it should be in config)
    # The loop above handles it if it's in config. If not in config, we might want a fallback?
    # The user said "store tools description and enabled flag in the graph config".
    # So we expect it to be there.

    return available_tools


async def execute_tool(tool_name: str, reasoning: str, **kwargs: Any) -> Any:
    tool_info = RETRIEVAL_AGENT_TOOLS.get(tool_name)
    if not tool_info:
        raise ValueError(f"Tool {tool_name} not found")

    tool_impl = tool_info.get("tool_impl")
    if not tool_impl:
        # Exit tool has no implementation
        if tool_name == "exit":
            return None
        raise ValueError(f"Tool {tool_name} has no implementation")

    return await tool_impl(**kwargs, **observability_overrides(description=reasoning))
