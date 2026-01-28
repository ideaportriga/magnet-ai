from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Annotated, Any
from uuid import UUID, uuid4

from litestar import Controller, Request, post
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.exceptions import ClientException
from litestar.params import Body, Parameter
from litestar.status_codes import HTTP_202_ACCEPTED, HTTP_200_OK
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.tags import TagNames
from services.agents.conversations import get_last_conversation_by_client_id
from core.db.models.knowledge_graph import KnowledgeGraph
from core.domain.agent_conversation.service import AgentConversationService
from core.domain.knowledge_graph.schemas import (
    KnowledgeGraphAgentResponse,
)
from services.knowledge_graph.content_config_services import (
    get_graph_embedding_model,
    get_graph_settings,
)
from services.knowledge_graph.retrievers.agent_retriever.agent import (
    continue_conversation,
    start_conversation,
)
from services.knowledge_graph.retrievers.agent_retriever.tools.find_chunks_by_similarity import (
    findChunksBySimilarity,
)
from services.knowledge_graph.retrievers.agent_retriever.tools.find_documents_by_metadata import (
    findDocumentsByMetadata,
)
from core.domain.knowledge_graph.service import KnowledgeGraphDocumentService
from open_ai.utils_new import get_embeddings
from services.knowledge_graph.sources.api_ingest import ApiIngestDataSource
from services.knowledge_graph.sources.api_ingest.api_ingest_source import (
    run_background_ingest,
)
from services.observability import (
    observability_context,
    observability_overrides,
    observe,
)

logger = logging.getLogger(__name__)


async def _resolve_graph_id_or_name(
    db_session: AsyncSession, graph_id_or_name: str
) -> UUID:
    """Resolve a Knowledge Graph identifier.

    Accepts either:
    - UUID string (matches KnowledgeGraph.id)
    - system name string (matches KnowledgeGraph.system_name; case-insensitive)
    """

    raw = str(graph_id_or_name or "").strip()
    if not raw:
        raise ClientException("Knowledge Graph identifier is required")

    parsed_uuid: UUID | None = None
    try:
        parsed_uuid = UUID(raw)
    except Exception:
        parsed_uuid = None

    # Prefer exact id match when the input parses as a UUID.
    if parsed_uuid is not None:
        result = await db_session.execute(
            select(KnowledgeGraph.id).where(KnowledgeGraph.id == parsed_uuid)
        )
        if result.scalar_one_or_none() is not None:
            return parsed_uuid

    # Fallback to system_name (case-insensitive).
    result = await db_session.execute(
        select(KnowledgeGraph.id).where(
            func.lower(KnowledgeGraph.system_name) == raw.lower()
        )
    )
    resolved = result.scalar_one_or_none()
    if resolved is None:
        raise ClientException("Knowledge Graph not found")

    return resolved if isinstance(resolved, UUID) else UUID(str(resolved))


class KnowledgeGraphIngestJsonRequest(BaseModel):
    """JSON payload for Knowledge Graph ingestion (plain text only)."""

    content: str | None = Field(
        default=None,
        description=(
            "Plain text to ingest into the Knowledge Graph. "
            "This field is required for `application/json` requests."
        ),
        examples=["Here is the content I want to ingest..."],
    )
    filename: str | None = Field(
        default=None,
        description=(
            "Optional logical filename for the plain text payload. "
            "If omitted, a generated ingestion ID is used."
        ),
        examples=["notes.txt", "meeting-notes"],
    )
    source_name: str | None = Field(
        default=None,
        description=(
            "Optional name of the API ingest source to create/reuse under this graph. "
            "Defaults to `API Ingest` if omitted or blank."
        ),
        examples=["API Ingest", "Support Tickets"],
    )

    model_config = ConfigDict(extra="ignore")


class KnowledgeGraphIngestMultipartRequest(BaseModel):
    """Multipart/form-data payload for Knowledge Graph ingestion (plain text and/or file)."""

    source_name: str | None = Field(
        default=None,
        description=(
            "Optional name of the API ingest source to create/reuse under this graph. "
            "Defaults to `API Ingest` if omitted or blank."
        ),
        examples=["API Ingest", "Support Tickets"],
    )
    content: str | None = Field(
        default=None,
        description=(
            "Plain text to ingest. You can provide `content`, `file`, or both. "
            "If both are provided, both will be ingested."
        ),
        examples=["Here is the content I want to ingest..."],
    )
    filename: str | None = Field(
        default=None,
        description=(
            "Optional logical filename for the `content` payload. "
            "If omitted, a generated ingestion ID is used."
        ),
        examples=["notes.txt", "meeting-notes"],
    )
    file: UploadFile | None = Field(
        default=None,
        description=(
            "File to ingest into the Knowledge Graph. This field is only applicable for multipart/form-data requests."
        ),
    )

    model_config = ConfigDict(extra="ignore", arbitrary_types_allowed=True)


class KnowledgeGraphIngestAcceptedResponse(BaseModel):
    ingestion_id: str
    source_id: str
    source_name: str
    trace_id: str | None = None
    status: str = "accepted"


@dataclass(frozen=True, slots=True)
class _IngestItem:
    kind: str  # "text" | "file"
    filename: str
    text: str | None = None
    file_bytes: bytes | None = None


class KnowledgeGraphAskRequest(BaseModel):
    """Ask a question against a knowledge graph using the Knowledge Graph agent."""

    message: str = Field(
        ..., min_length=1, description="User message to send to the agent."
    )
    conversation_id: UUID | None = None
    client_id: str | None = Field(
        default=None,
        description=(
            "Optional client-side identifier (e.g., user_id + page_name) to retrieve "
            "or create a conversation without storing conversation_id on the client side. "
            "If both conversation_id and client_id are provided, conversation_id takes precedence."
        ),
        examples=["user123_kg_dashboard"],
    )
    filter_documents_by_metadata: str | dict[str, Any] | None = Field(
        default=None,
        description=(
            "Optional metadata filter expression to constrain documents. "
            "May be provided as a JSON object or as a stringified JSON value."
        ),
    )
    trace_id: str | None = None

    model_config = ConfigDict(extra="ignore")


class KnowledgeGraphSearchRequest(BaseModel):
    """Semantic search over a knowledge graph (chunk-level)."""

    query: str = Field(..., min_length=1)
    limit: int = Field(default=10, ge=1, le=50)
    min_score: float = Field(default=0.5, ge=0.0, le=1.0)
    filter_documents_by_ids: list[UUID] | None = None
    filter_documents_by_metadata: str | dict[str, Any] | None = Field(
        default=None,
        description=(
            "Optional metadata filter expression to constrain documents. "
            "May be provided as a JSON object or as a stringified JSON value."
        ),
    )

    model_config = ConfigDict(extra="ignore")


class KnowledgeGraphSearchResponse(BaseModel):
    """Search response for chunk-level semantic search."""

    chunks: list[dict[str, Any]] = Field(default_factory=list)
    trace_id: str | None = None


class KnowledgeGraphDocumentSearchRequest(BaseModel):
    """Semantic search over a knowledge graph (document-level summary)."""

    query: str = Field(..., min_length=1)
    limit: int = Field(default=10, ge=1, le=50)
    min_score: float = Field(default=0.5, ge=0.0, le=1.0)
    filter_documents_by_metadata: str | dict[str, Any] | None = Field(
        default=None,
        description=(
            "Optional metadata filter expression to constrain documents. "
            "May be provided as a JSON object or as a stringified JSON value."
        ),
    )

    model_config = ConfigDict(extra="ignore")


class KnowledgeGraphDocumentSearchResponse(BaseModel):
    """Search response for document-level summary semantic search."""

    documents: list[dict[str, Any]] = Field(default_factory=list)
    trace_id: str | None = None


class UserKnowledgeGraphController(Controller):
    """User-facing Knowledge Graph endpoints."""

    path = "/knowledge_graph"
    tags = [TagNames.UserKnowledgeGraph]

    @post(
        "/{graph_id_or_name:str}/agent/ask",
        summary="Ask Knowledge Graph Agent",
        description=(
            "Runs the Knowledge Graph Agent against the specified graph. "
            "Supports continuing a prior conversation via `conversation_id`."
        ),
    )
    async def ask(
        self,
        graph_id_or_name: Annotated[
            str,
            Parameter(
                title="Knowledge Graph ID or System Name",
                description="The UUID or System Name of the Knowledge Graph to query.",
            ),
        ],
        db_session: AsyncSession,
        data: KnowledgeGraphAskRequest,
    ) -> KnowledgeGraphAgentResponse:
        graph_id = await _resolve_graph_id_or_name(db_session, graph_id_or_name)

        # Validate embedding model exists (required for retrieval)
        embedding_model = await get_graph_embedding_model(db_session, graph_id)
        if not embedding_model:
            raise ClientException(
                "Embedding model is not configured in knowledge graph settings."
            )

        tool_inputs: dict[str, Any] | None = None
        raw_meta_filter = data.filter_documents_by_metadata
        if raw_meta_filter is not None:
            has_value = True
            if isinstance(raw_meta_filter, str) and not raw_meta_filter.strip():
                has_value = False
            if isinstance(raw_meta_filter, dict) and len(raw_meta_filter) == 0:
                has_value = False

            if has_value:
                tool_inputs = {"findDocumentsByMetadata": {"filter": raw_meta_filter}}

        # Determine if we're continuing an existing conversation
        existing_conversation = None

        # Priority 1: Look up by conversation_id
        if data.conversation_id is not None:
            conversation_service = AgentConversationService(session=db_session)
            existing_conversation = await conversation_service.get_one_or_none(
                id=str(data.conversation_id)
            )
            if existing_conversation is None:
                raise ClientException("Conversation not found")

        # Priority 2: Look up by client_id if conversation_id wasn't provided
        elif data.client_id is not None:
            try:
                existing_conversation = await get_last_conversation_by_client_id(
                    data.client_id
                )
            except Exception:
                # If lookup fails, proceed to create new conversation
                existing_conversation = None

        # Validate that existing conversation belongs to Knowledge Graph agent
        if existing_conversation is not None:
            if (
                existing_conversation.agent
                and existing_conversation.agent != "KNOWLEDGE_GRAPH_AGENT"
            ):
                raise ClientException(
                    "Conversation does not belong to Knowledge Graph agent"
                )

            # Continue existing conversation
            result = await continue_conversation(
                db_session,
                graph_id,
                data.message,
                existing_conversation.id,
                tool_inputs=tool_inputs,
                **observability_overrides(trace_id=existing_conversation.trace_id),
            )
        else:
            # Start new conversation (with optional client_id)
            result = await start_conversation(
                db_session,
                graph_id,
                data.message,
                client_id=data.client_id,
                tool_inputs=tool_inputs,
                **observability_overrides(trace_id=data.trace_id),
            )

        return KnowledgeGraphAgentResponse(**result.model_dump())

    @observe(
        name="Search knowledge graph",
        channel="production",
        source="Runtime API",
    )
    @post(
        "/{graph_id_or_name:str}/chunks/search",
        summary="Search Knowledge Graph chunks",
        description=(
            "Performs vector similarity search over the graph's chunks. "
            "Optionally constrains results using a structured `filter_documents_by_metadata` and/or "
            "`filter_documents_by_ids`."
        ),
        status_code=HTTP_200_OK,
    )
    async def search(
        self,
        graph_id_or_name: Annotated[
            str,
            Parameter(
                title="Knowledge Graph ID or System Name",
                description="The UUID or System Name of the Knowledge Graph to search.",
            ),
        ],
        db_session: AsyncSession,
        data: KnowledgeGraphSearchRequest,
    ) -> KnowledgeGraphSearchResponse:
        graph_id = await _resolve_graph_id_or_name(db_session, graph_id_or_name)

        # Validate embedding model exists (required for semantic search)
        embedding_model = await get_graph_embedding_model(db_session, graph_id)
        if not embedding_model:
            raise ClientException(
                "Embedding model is not configured in knowledge graph settings."
            )

        # Optional: compile metadata filter into a safe SQL predicate
        doc_filter_where_sql: str | None = None
        doc_filter_where_params: dict[str, Any] | None = None

        if data.filter_documents_by_metadata is not None:
            settings = await get_graph_settings(db_session, graph_id)
            metadata_field_definitions: list[dict[str, Any]] = []
            try:
                metadata_cfg = (
                    settings.get("metadata") if isinstance(settings, dict) else {}
                )
                raw_defs = (
                    metadata_cfg.get("field_definitions")
                    if isinstance(metadata_cfg, dict)
                    else None
                )
                if isinstance(raw_defs, list):
                    metadata_field_definitions = [
                        d for d in raw_defs if isinstance(d, dict)
                    ]
            except Exception:  # noqa: BLE001
                metadata_field_definitions = []

            _, loop_state, _step = await findDocumentsByMetadata(
                db_session,
                graph_id,
                args={
                    "reasoning": "External search metadata filter",
                    "filter": data.filter_documents_by_metadata,
                },
                iteration=1,
                field_definitions=metadata_field_definitions,
            )
            doc_filter_where_sql = loop_state.get("doc_filter_where_sql")
            doc_filter_where_params = loop_state.get("doc_filter_where_params")

            if doc_filter_where_sql is None:
                raise ClientException("Invalid or empty metadata_filter")

        doc_filter_ids = [str(x) for x in (data.filter_documents_by_ids or [])]

        chunks = await findChunksBySimilarity(
            db_session=db_session,
            graph_id=graph_id,
            q=data.query,
            embedding_model=embedding_model,
            limit=int(data.limit),
            min_score=float(data.min_score),
            doc_filter_ids=doc_filter_ids,
            doc_filter_where_sql=doc_filter_where_sql,
            doc_filter_where_params=doc_filter_where_params,
        )

        trace_id = observability_context.get_current_trace_id()[:8]
        return KnowledgeGraphSearchResponse(chunks=chunks, trace_id=trace_id)

    @observe(
        name="Search knowledge graph documents",
        channel="production",
        source="Runtime API",
    )
    @post(
        "/{graph_id_or_name:str}/documents/search",
        summary="Search Knowledge Graph documents by summary",
        description=(
            "Performs vector similarity search over the graph's document summaries. "
            "Optionally constrains results using a structured `filter_documents_by_metadata`."
        ),
        status_code=HTTP_200_OK,
    )
    async def search_documents(
        self,
        graph_id_or_name: Annotated[
            str,
            Parameter(
                title="Knowledge Graph ID or System Name",
                description="The UUID or System Name of the Knowledge Graph to search.",
            ),
        ],
        db_session: AsyncSession,
        data: KnowledgeGraphDocumentSearchRequest,
    ) -> KnowledgeGraphDocumentSearchResponse:
        graph_id = await _resolve_graph_id_or_name(db_session, graph_id_or_name)

        # Validate embedding model exists (required for semantic search)
        embedding_model = await get_graph_embedding_model(db_session, graph_id)
        if not embedding_model:
            raise ClientException(
                "Embedding model is not configured in knowledge graph settings."
            )

        # TODO: Implement metadata filtering for document search endpoint
        # Similar to chunk search endpoint using findDocumentsByMetadata
        doc_filter_where_sql: str | None = None
        doc_filter_where_params: dict[str, Any] | None = None

        # Generate query embedding
        query_vector = await get_embeddings(data.query, embedding_model)

        # Perform document search with metadata filtering
        documents = await KnowledgeGraphDocumentService().search_documents(
            db_session=db_session,
            graph_id=graph_id,
            query_vector=query_vector,
            limit=int(data.limit),
            min_score=float(data.min_score),
            doc_filter_where_sql=doc_filter_where_sql,
            doc_filter_where_params=doc_filter_where_params,
        )

        trace_id = observability_context.get_current_trace_id()[:8]
        return KnowledgeGraphDocumentSearchResponse(
            documents=documents, trace_id=trace_id
        )

    @observe(
        name="Ingest into knowledge graph",
        channel="production",
        source="Runtime API",
    )
    @post(
        "/{graph_id_or_name:str}/ingest",
        status_code=HTTP_202_ACCEPTED,
        summary="Ingest text or a file into Knowledge Graph",
        description=(
            "Accepts ingestion payload quickly and processes it asynchronously in the background.\n\n"
            "Request body can be sent as either:\n"
            "- `application/json` (plain text): `content`, optional `filename`, optional `source_name`\n"
            "- `multipart/form-data` (plain text and/or file): optional `content`, optional `filename`, optional `source_name`, optional `file`\n\n"
            "At least one of `content` or `file` must be provided.\n\n"
            "If no source is specified, a default 'api_ingest' source is created (or reused). "
            "Provide `source_name` to create/use a separate source."
        ),
    )
    async def ingest(
        self,
        graph_id_or_name: Annotated[
            str,
            Parameter(
                title="Knowledge Graph ID or System Name",
                description=(
                    "The UUID or System Name of the Knowledge Graph to ingest content into."
                ),
            ),
        ],
        request: Request,
        db_session: AsyncSession,
        json_data: Annotated[
            KnowledgeGraphIngestJsonRequest | None,
            Body(
                title="Ingest payload (application/json)",
                description=(
                    "Use `application/json` for plain text only ingestion. "
                    "For file upload (and/or mixed text+file), use the multipart/form-data variant."
                ),
            ),
        ] = None,
        form_data: Annotated[
            KnowledgeGraphIngestMultipartRequest | None,
            Body(
                title="Ingest payload (multipart/form-data)",
                description=(
                    "Use `multipart/form-data` to upload a file and/or provide plain text. "
                    "Form fields: `source_name`, `content`, `filename`, `file`."
                ),
                media_type=RequestEncodingType.MULTI_PART,
            ),
        ] = None,
    ) -> KnowledgeGraphIngestAcceptedResponse:
        ctype = (request.headers.get("content-type") or "").lower()

        graph_id = await _resolve_graph_id_or_name(db_session, graph_id_or_name)

        source_name: str | None = None
        content: str | None = None
        filename: str | None = None
        upload: UploadFile | None = None

        if form_data is not None:
            source_name = form_data.source_name
            content = form_data.content
            filename = form_data.filename
            upload = form_data.file
        elif json_data is not None:
            source_name = json_data.source_name
            content = json_data.content
            filename = json_data.filename
        else:
            # Fallback for clients that don't match the expected parsing path (keeps behavior stable).
            if ctype.startswith("multipart/"):
                form = await request.form()
                source_name = form.get("source_name")
                content = form.get("content")
                filename = form.get("filename")
                upload = form.get("file")
            else:
                body = await request.json()
                data = KnowledgeGraphIngestJsonRequest.model_validate(body)
                source_name = data.source_name
                content = data.content
                filename = data.filename

        normalized_source_name = (source_name or "API Ingest").strip() or "API Ingest"

        # Build ingest items (we accept text and/or a file)
        items: list[_IngestItem] = []
        ingestion_id = str(uuid4())

        if upload is not None:
            upload_filename = (upload.filename or "").strip() or "upload.bin"
            file_bytes = await upload.read()
            items.append(
                _IngestItem(
                    kind="file",
                    filename=upload_filename,
                    file_bytes=file_bytes,
                )
            )

        if isinstance(content, str) and content.strip():
            text_filename = (filename or "").strip()
            if not text_filename:
                text_filename = ingestion_id
            elif "." not in text_filename:
                text_filename = f"{text_filename}.txt"

            items.append(
                _IngestItem(
                    kind="text",
                    filename=text_filename,
                    text=content,
                )
            )

        if not items:
            raise ClientException("Provide 'content' and/or 'file' to ingest")

        # Create or reuse the (graph_id, type=api_ingest, name=source_name) source
        source = await ApiIngestDataSource(
            source_name=normalized_source_name
        ).get_or_create_source(db_session, graph_id)

        # Spawn background ingestion (do not await)
        asyncio.create_task(
            run_background_ingest(
                ingestion_id=ingestion_id,
                graph_id=graph_id,
                source_id=UUID(str(source.id)),
                items=items,
            )
        )

        trace_id = observability_context.get_current_trace_id()[:8]
        return KnowledgeGraphIngestAcceptedResponse(
            ingestion_id=ingestion_id,
            source_id=str(source.id),
            source_name=source.name,
            trace_id=trace_id,
        )
