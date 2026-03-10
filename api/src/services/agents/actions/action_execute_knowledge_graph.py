from logging import getLogger
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config.app import alchemy
from core.db.models.knowledge_graph import KnowledgeGraph
from services.agents.models import AgentActionCallResponse
from services.observability import observability_context, observe
from services.observability.models import SpanType

logger = getLogger(__name__)

DEFAULT_LIMIT = 5
DEFAULT_MIN_SCORE = 0.5


async def _resolve_graph_id(
    system_name: str,
) -> UUID:
    """Resolve a Knowledge Graph by system_name (case-insensitive) or UUID."""
    raw = system_name.strip()
    if not raw:
        raise ValueError("Knowledge Graph system name is required")

    async with alchemy.get_session() as session:
        # Try parsing as UUID first
        parsed_uuid: UUID | None = None
        try:
            parsed_uuid = UUID(raw)
        except Exception:
            parsed_uuid = None

        if parsed_uuid is not None:
            result = await session.execute(
                select(KnowledgeGraph.id).where(KnowledgeGraph.id == parsed_uuid)
            )
            if result.scalar_one_or_none() is not None:
                return parsed_uuid

        # Fallback to system_name (case-insensitive)
        result = await session.execute(
            select(KnowledgeGraph.id).where(
                func.lower(KnowledgeGraph.system_name) == raw.lower()
            )
        )
        resolved = result.scalar_one_or_none()
        if resolved is None:
            raise LookupError(
                f"Knowledge Graph with system name '{system_name}' not found"
            )

        return resolved if isinstance(resolved, UUID) else UUID(str(resolved))


# ---------------------------------------------------------------------------
# Per-tool execution helpers
# ---------------------------------------------------------------------------


async def _execute_find_chunks(
    db_session: AsyncSession,
    graph_id: UUID,
    graph_system_name: str,
    embedding_model: str,
    arguments: dict,
) -> AgentActionCallResponse:
    """Execute findChunksBySimilarity and return formatted content."""
    from services.knowledge_graph.retrievers.agent_retriever.tools.find_chunks_by_similarity import (
        findChunksBySimilarity,
    )

    query = arguments.get("query")
    if not query:
        raise ValueError("Cannot call findChunksBySimilarity - 'query' is missing")

    limit = int(arguments.get("limit", DEFAULT_LIMIT))
    min_score = float(arguments.get("min_score", DEFAULT_MIN_SCORE))

    chunks = await findChunksBySimilarity(
        db_session=db_session,
        graph_id=graph_id,
        q=query,
        embedding_model=embedding_model,
        limit=limit,
        min_score=min_score,
        doc_filter_ids=[],
    )

    if not chunks:
        content = "No relevant chunks found in the knowledge graph."
    else:
        content_parts: list[str] = []
        for chunk in chunks:
            title = chunk.get("title") or chunk.get("name") or "Untitled"
            text = chunk.get("content") or ""
            score = chunk.get("score")
            doc_name = chunk.get("document_name") or ""

            header = f"## {title}"
            if doc_name:
                header += f" (from: {doc_name})"
            if score is not None:
                header += f" [score: {score:.2f}]"
            content_parts.append(f"{header}\n{text}")

        content = "\n\n".join(content_parts)

    return AgentActionCallResponse(
        content=content,
        verbose_details={
            "graph_system_name": graph_system_name,
            "graph_id": str(graph_id),
            "tool": "findChunksBySimilarity",
            "query": query,
            "limit": limit,
            "min_score": min_score,
            "chunks_count": len(chunks) if chunks else 0,
            "chunks": chunks or [],
        },
    )


async def _execute_find_documents_by_summary(
    db_session: AsyncSession,
    graph_id: UUID,
    graph_system_name: str,
    embedding_model: str,
    arguments: dict,
) -> AgentActionCallResponse:
    """Execute findDocumentsBySummarySimilarity and return document summaries."""
    from core.domain.knowledge_graph.service import KnowledgeGraphDocumentService
    from open_ai.utils_new import get_embeddings

    query = arguments.get("query")
    if not query:
        raise ValueError(
            "Cannot call findDocumentsBySummarySimilarity - 'query' is missing"
        )

    limit = int(arguments.get("limit", DEFAULT_LIMIT))
    min_score = float(arguments.get("min_score", DEFAULT_MIN_SCORE))

    vec = await get_embeddings(query, embedding_model)
    docs = await KnowledgeGraphDocumentService().search_documents(
        db_session,
        graph_id=graph_id,
        query_vector=vec,
        limit=limit,
    )
    filtered_docs = [d for d in docs if d.get("score", 0.0) >= min_score]

    if not filtered_docs:
        content = "No relevant documents found in the knowledge graph."
    else:
        content_parts: list[str] = []
        for doc in filtered_docs:
            name = doc.get("name") or doc.get("title") or "Untitled"
            summary = doc.get("summary") or ""
            score = doc.get("score")

            header = f"## {name}"
            if score is not None:
                header += f" [score: {score:.2f}]"
            content_parts.append(f"{header}\n{summary}" if summary else header)

        content = "\n\n".join(content_parts)

    return AgentActionCallResponse(
        content=content,
        verbose_details={
            "graph_system_name": graph_system_name,
            "graph_id": str(graph_id),
            "tool": "findDocumentsBySummarySimilarity",
            "query": query,
            "limit": limit,
            "min_score": min_score,
            "documents_count": len(filtered_docs),
        },
    )


async def _execute_find_documents_by_metadata(
    db_session: AsyncSession,
    graph_id: UUID,
    graph_system_name: str,
    arguments: dict,
) -> AgentActionCallResponse:
    """Execute findDocumentsByMetadata (simplified standalone version)."""
    from services.knowledge_graph.retrievers.agent_retriever.tools.find_documents_by_metadata import (
        findDocumentsByMetadata,
    )

    filter_expr = arguments.get("filter")
    if not filter_expr:
        raise ValueError("Cannot call findDocumentsByMetadata - 'filter' is missing")

    try:
        result = await findDocumentsByMetadata(
            db_session=db_session,
            graph_id=graph_id,
            args={"filter": filter_expr, "reasoning": "Agent action call"},
            iteration=0,
            tool_name="findDocumentsByMetadata",
        )
        payload = result.tool_payload
        matched = payload.get("matched_documents", 0)
        content = f"Metadata filter matched {matched} document(s)."
    except Exception as e:
        content = f"Metadata filter failed: {e}"
        matched = 0

    return AgentActionCallResponse(
        content=content,
        verbose_details={
            "graph_system_name": graph_system_name,
            "graph_id": str(graph_id),
            "tool": "findDocumentsByMetadata",
            "filter": filter_expr,
            "matched_documents": matched,
        },
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


@observe(
    name="Call Knowledge Graph Tool",
    description="Execute a specific knowledge graph retriever tool.",
    type=SpanType.TOOL,
)
async def action_execute_knowledge_graph(
    tool_provider: str,
    tool_system_name: str,
    arguments: dict,
    variables: dict[str, str] | None = None,
) -> AgentActionCallResponse:
    """Execute a knowledge graph tool.

    Parameters
    ----------
    tool_provider:
        The KG system_name (identifies which graph to query).
    tool_system_name:
        The specific tool to run (e.g. ``findChunksBySimilarity``).
    arguments:
        Tool-specific arguments produced by the LLM.
    variables:
        Agent variable substitutions (unused for now).
    """

    observability_context.update_current_span(
        input={
            "Knowledge Graph": tool_provider,
            "Tool": tool_system_name,
            "Arguments": arguments,
        },
    )

    graph_id = await _resolve_graph_id(tool_provider)

    async with alchemy.get_session() as db_session:
        # Lazy import to avoid circular dependency
        from services.knowledge_graph.content_config_services import (
            get_graph_embedding_model,
        )

        match tool_system_name:
            case "findChunksBySimilarity":
                embedding_model = await get_graph_embedding_model(db_session, graph_id)
                if not embedding_model:
                    raise RuntimeError(
                        f"Embedding model is not configured for Knowledge Graph '{tool_provider}'"
                    )
                return await _execute_find_chunks(
                    db_session, graph_id, tool_provider, embedding_model, arguments
                )

            case "findDocumentsBySummarySimilarity":
                embedding_model = await get_graph_embedding_model(db_session, graph_id)
                if not embedding_model:
                    raise RuntimeError(
                        f"Embedding model is not configured for Knowledge Graph '{tool_provider}'"
                    )
                return await _execute_find_documents_by_summary(
                    db_session, graph_id, tool_provider, embedding_model, arguments
                )

            case "findDocumentsByMetadata":
                return await _execute_find_documents_by_metadata(
                    db_session, graph_id, tool_provider, arguments
                )

            case _:
                raise ValueError(
                    f"Unknown Knowledge Graph tool '{tool_system_name}' "
                    f"for graph '{tool_provider}'"
                )
