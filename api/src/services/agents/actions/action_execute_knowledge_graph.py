from logging import getLogger
from uuid import UUID

from sqlalchemy import func, select

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


@observe(
    name="Call Knowledge Graph",
    description="Search knowledge graph chunks by semantic similarity. The agent determines what query to execute against the knowledge graph.",
    type=SpanType.TOOL,
)
async def action_execute_knowledge_graph(
    tool_system_name: str,
    arguments: dict,
    variables: dict[str, str] | None = None,
) -> AgentActionCallResponse:
    query = arguments.get("query")
    assert query, "Cannot call Knowledge Graph tool - user's query is missing"

    limit = arguments.get("limit", DEFAULT_LIMIT)
    min_score = arguments.get("min_score", DEFAULT_MIN_SCORE)

    observability_context.update_current_span(
        input={
            "Knowledge Graph system name": tool_system_name,
            "Query": query,
            "Limit": limit,
            "Min Score": min_score,
        },
    )

    graph_id = await _resolve_graph_id(tool_system_name)

    async with alchemy.get_session() as db_session:
        # Lazy imports to avoid circular dependency
        from services.knowledge_graph.content_config_services import (
            get_graph_embedding_model,
        )
        from services.knowledge_graph.retrievers.agent_retriever.tools.find_chunks_by_similarity import (
            findChunksBySimilarity,
        )

        embedding_model = await get_graph_embedding_model(db_session, graph_id)
        if not embedding_model:
            raise RuntimeError(
                f"Embedding model is not configured for Knowledge Graph '{tool_system_name}'"
            )

        try:
            chunks = await findChunksBySimilarity(
                db_session=db_session,
                graph_id=graph_id,
                q=query,
                embedding_model=embedding_model,
                limit=int(limit),
                min_score=float(min_score),
                doc_filter_ids=[],
            )
        except Exception as e:
            raise RuntimeError(f"Failed to search Knowledge Graph: {e}")

    if not chunks:
        content = "No relevant results found in the knowledge graph."
    else:
        content_parts = []
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

    result = AgentActionCallResponse(
        content=content,
        verbose_details={
            "graph_system_name": tool_system_name,
            "graph_id": str(graph_id),
            "query": query,
            "limit": limit,
            "min_score": min_score,
            "chunks_count": len(chunks) if chunks else 0,
            "chunks": chunks or [],
        },
    )

    return result
