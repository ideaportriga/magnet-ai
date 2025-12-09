from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from advanced_alchemy.extensions.litestar import repository, service
from litestar.exceptions import ClientException, NotFoundException
from litestar.status_codes import HTTP_415_UNSUPPORTED_MEDIA_TYPE
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models.knowledge_graph import KnowledgeGraph, KnowledgeGraphSource
from core.domain.ai_models.service import AIModelsService
from core.domain.agent_conversation.service import AgentConversationService
from core.domain.knowledge_graph.schemas import (
    KnowledgeGraphChunkExternalSchema,
    KnowledgeGraphChunkListResponse,
    KnowledgeGraphCreateRequest,
    KnowledgeGraphCreateResponse,
    KnowledgeGraphDocumentDetailSchema,
    KnowledgeGraphDocumentExternalSchema,
    KnowledgeGraphExternalSchema,
    KnowledgeGraphRetrievalPreviewResponse,
    KnowledgeGraphSourceCreateRequest,
    KnowledgeGraphSourceCreateResponse,
    KnowledgeGraphSourceExternalSchema,
    KnowledgeGraphSourceUpdateRequest,
    KnowledgeGraphUpdateRequest,
    KnowledgeGraphUpdateResponse,
)
from services.agents.models import (
    AgentConversationDataWithMessages,
    AgentConversationMessageAssistant,
    AgentConversationMessageUser,
)
from services.knowledge_graph import (
    get_content_config,
    get_default_content_configs,
    get_default_retrieval_settings,
    load_content_from_bytes,
)
from services.knowledge_graph.retrievers import run_agentic_retrieval
from services.knowledge_graph.sources import (
    ManualUploadDataSource,
    SharePointDataSource,
)
from services.knowledge_graph.store_services import (
    chunks_table_name,
    docs_table_name,
    drop_graph_tables,
)
from services.observability import observe, observability_context
from utils.datetime_utils import utc_now_isoformat, utc_now


class KnowledgeGraphService(service.SQLAlchemyAsyncRepositoryService[KnowledgeGraph]):
    """Service for Knowledge Graph operations."""

    async def list_graphs(
        self, db_session: AsyncSession
    ) -> list[KnowledgeGraphExternalSchema]:
        result = await db_session.execute(
            select(KnowledgeGraph).order_by(KnowledgeGraph.created_at.desc())
        )
        graphs = result.scalars().all()
        results: list[KnowledgeGraphExternalSchema] = []
        for graph in graphs:
            # Dynamic per-graph counts
            docs_table = docs_table_name(graph.id)
            ch_table = chunks_table_name(graph.id)
            try:
                docs_count_res = await db_session.execute(
                    text(f"SELECT COUNT(*) FROM {docs_table}")
                )
                documents_count = int(docs_count_res.scalar_one() or 0)
            except Exception:
                documents_count = 0
            try:
                chunks_count_res = await db_session.execute(
                    text(f"SELECT COUNT(*) FROM {ch_table}")
                )
                chunks_count = int(chunks_count_res.scalar_one() or 0)
            except Exception:
                chunks_count = 0
            results.append(
                KnowledgeGraphExternalSchema(
                    id=str(graph.id),
                    name=graph.name,
                    system_name=getattr(graph, "system_name", None),
                    description=getattr(graph, "description", None),
                    documents_count=int(documents_count or 0),
                    chunks_count=int(chunks_count or 0),
                    created_at=graph.created_at.isoformat()
                    if graph.created_at
                    else None,
                    updated_at=graph.updated_at.isoformat()
                    if graph.updated_at
                    else None,
                )
            )
        return results

    async def get_graph(
        self, db_session: AsyncSession, graph_id: UUID
    ) -> KnowledgeGraphExternalSchema:
        graph_res = await db_session.execute(
            select(KnowledgeGraph).where(KnowledgeGraph.id == graph_id)
        )
        graph = graph_res.scalar_one_or_none()
        if not graph:
            raise NotFoundException("Graph not found")

        # Dynamic per-graph counts
        docs_table = docs_table_name(graph.id)
        ch_table = chunks_table_name(graph.id)
        try:
            docs_count_res = await db_session.execute(
                text(f"SELECT COUNT(*) FROM {docs_table}")
            )
            documents_count = int(docs_count_res.scalar_one() or 0)
        except Exception:
            documents_count = 0
        try:
            chunks_count_res = await db_session.execute(
                text(f"SELECT COUNT(*) FROM {ch_table}")
            )
            chunks_count = int(chunks_count_res.scalar_one() or 0)
        except Exception:
            chunks_count = 0
        return KnowledgeGraphExternalSchema(
            id=str(graph.id),
            name=graph.name,
            system_name=getattr(graph, "system_name", None),
            description=getattr(graph, "description", None),
            documents_count=int(documents_count or 0),
            chunks_count=int(chunks_count or 0),
            settings=getattr(graph, "settings", None)
            if hasattr(graph, "settings")
            else None,
            created_at=graph.created_at.isoformat() if graph.created_at else None,
            updated_at=graph.updated_at.isoformat() if graph.updated_at else None,
        )

    async def create_graph(
        self, db_session: AsyncSession, data: KnowledgeGraphCreateRequest
    ) -> KnowledgeGraphCreateResponse:
        system_name = (
            (data.system_name or data.name)
            .upper()
            .replace(" ", "_")
            .replace(".", "_")
            .strip(" _")
        )

        default_configs = get_default_content_configs()
        retrieval_settings = get_default_retrieval_settings()
        settings: dict[str, Any] | None = {
            "chunking": {
                "content_settings": [cfg.model_dump() for cfg in default_configs],
            },
            **retrieval_settings,
        }

        # Set default embedding model if it exists
        try:
            models_service = AIModelsService(session=db_session)
            default_embedding = await models_service.get_one_or_none(
                type="embeddings", is_default=True
            )
            if default_embedding:
                indexing_cfg = dict((settings.get("indexing") or {}))
                indexing_cfg["embedding_model"] = default_embedding.system_name
                settings["indexing"] = indexing_cfg
        except Exception:
            # Non-fatal: proceed without default embedding if lookup fails
            pass

        created = await self.create(
            {
                "name": data.name,
                "system_name": system_name,
                "description": data.description,
                "settings": settings,
            }
        )

        return KnowledgeGraphCreateResponse(id=str(created.id))

    async def update_graph(
        self, graph_id: UUID, data: KnowledgeGraphUpdateRequest
    ) -> KnowledgeGraphUpdateResponse:
        existing = await self.repository.get(graph_id)

        update_payload: dict[str, Any] = {}

        if data.name is not None:
            update_payload["name"] = data.name
        if data.description is not None:
            update_payload["description"] = data.description

        # Base settings start from explicit payload if provided, otherwise existing
        settings_to_apply: dict[str, Any] | None = None
        if data.settings is not None:
            settings_to_apply = data.settings
        else:
            current_settings = getattr(existing, "settings", None) or {}
            if isinstance(current_settings, dict):
                settings_to_apply = dict(current_settings)

        if data.content_configs is not None:
            if settings_to_apply is None:
                settings_to_apply = {}
            chunking = dict(settings_to_apply.get("chunking") or {})
            chunking["content_settings"] = data.content_configs or []
            settings_to_apply["chunking"] = chunking

        if settings_to_apply is not None:
            update_payload["settings"] = settings_to_apply

        updated = await self.update(
            update_payload,
            item_id=graph_id,
            auto_commit=True,
            auto_refresh=True,
        )

        return KnowledgeGraphUpdateResponse(
            id=str(updated.id),
            name=updated.name,
            system_name=getattr(updated, "system_name", None),
            description=getattr(updated, "description", None),
        )

    async def delete_graph(self, db_session: AsyncSession, graph_id: UUID) -> None:
        """Delete a graph and drop its per-graph tables."""
        # Ensure the graph exists
        _ = await self.repository.get(graph_id)

        # Drop dynamic tables
        await drop_graph_tables(db_session, graph_id)
        await db_session.commit()

        # Remove graph record
        await self.delete(item_id=graph_id, auto_commit=True)

    async def upload_file(
        self, db_session: AsyncSession, graph_id: UUID, filename: str, file_bytes: bytes
    ) -> dict[str, str]:
        try:
            config = await get_content_config(
                db_session, graph_id, filename, source_type="upload"
            )
            if not config:
                raise ClientException(
                    f"Knowledge Graph does not support file type '{filename}'.",
                    status_code=HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                )

            content = load_content_from_bytes(file_bytes, config)
            total_pages = content["metadata"].get("total_pages")

            await ManualUploadDataSource().upload_and_process_document(
                db_session,
                graph_id,
                filename=filename,
                extracted_text=content["text"],
                total_pages=total_pages,
                config=config,
            )

            return {"status": "ok"}
        except ClientException:
            # Re-raise known client exceptions untouched
            raise
        except Exception as e:  # noqa: BLE001
            raise ClientException(f"File upload failed: {e}")

    @observe(name="Start conversation", channel="production", source="production")
    async def start_conversation(
        self,
        db_session: AsyncSession,
        graph_id: UUID,
        query: str,
    ) -> KnowledgeGraphRetrievalPreviewResponse:
        graph = await self.repository.get(graph_id)
        observability_context.update_current_trace(name=graph.name)

        conversation_service = AgentConversationService(session=db_session)
        now = utc_now()

        # Start a new conversation with the initial user message
        user_msg = AgentConversationMessageUser(
            id=uuid4(),
            content=query,
            created_at=now,
        )

        # Get current trace id to link conversation to trace
        trace_id = observability_context.get_current_trace_id()

        conversation_data = AgentConversationDataWithMessages(
            agent="KNOWLEDGE_GRAPH_AGENT",
            created_at=now,
            last_user_message_at=now,
            messages=[user_msg],
            client_id=None,
            trace_id=trace_id,
            analytics_id=None,
            variables=None,
        )
        conversation_record = await conversation_service.create(
            conversation_data.model_dump(), auto_commit=True
        )
        conversation = conversation_service.to_schema(
            conversation_record, schema_type=AgentConversationDataWithMessages
        )

        conversation_id_str = str(conversation.id)

        # Build chat history to run the retrieval agent
        chat_history: list[dict[str, Any]] = []
        for m in conversation.messages:
            if not getattr(m, "content", None):
                continue
            role_value = getattr(m.role, "value", m.role)
            chat_history.append({"role": role_value, "content": m.content})

        # Run agent over full conversation history
        preview = await run_agentic_retrieval(db_session, graph_id, chat_history)

        # Append assistant response to conversation
        assistant_msg = AgentConversationMessageAssistant(
            id=uuid4(),
            content=preview.content,
            created_at=utc_now(),
        )
        conversation.messages.append(assistant_msg)
        await conversation_service.update(
            item_id=str(conversation.id),
            data=conversation.model_dump(),
            auto_commit=True,
        )

        return preview.model_copy(update={"conversation_id": conversation_id_str})

    @observe(name="New user message", channel="production", source="production")
    async def continue_conversation(
        self,
        db_session: AsyncSession,
        graph_id: UUID,
        query: str,
        conversation_id: UUID,
    ) -> KnowledgeGraphRetrievalPreviewResponse:
        conversation_service = AgentConversationService(session=db_session)
        now = utc_now()

        conversation_record = await conversation_service.get_one_or_none(
            id=str(conversation_id)
        )

        if not conversation_record:
            raise NotFoundException("Conversation not found")

        # Continue existing conversation: append user message
        conversation = conversation_service.to_schema(
            conversation_record, schema_type=AgentConversationDataWithMessages
        )
        user_msg = AgentConversationMessageUser(
            id=uuid4(),
            content=query,
            created_at=now,
        )
        conversation.messages.append(user_msg)
        conversation.last_user_message_at = now
        await conversation_service.update(
            item_id=str(conversation.id),
            data=conversation.model_dump(),
            auto_commit=True,
        )

        conversation_id_str = str(conversation.id)

        # Build chat history to run the retrieval agent
        chat_history: list[dict[str, Any]] = []
        for m in conversation.messages:
            if not getattr(m, "content", None):
                continue
            role_value = getattr(m.role, "value", m.role)
            chat_history.append({"role": role_value, "content": m.content})

        # Run agent over full conversation history
        preview = await run_agentic_retrieval(db_session, graph_id, chat_history)

        # Append assistant response to conversation
        assistant_msg = AgentConversationMessageAssistant(
            id=uuid4(),
            content=preview.content,
            created_at=utc_now(),
        )
        conversation.messages.append(assistant_msg)
        await conversation_service.update(
            item_id=str(conversation.id),
            data=conversation.model_dump(),
            auto_commit=True,
        )

        return preview.model_copy(update={"conversation_id": conversation_id_str})

    class Repo(repository.SQLAlchemyAsyncRepository[KnowledgeGraph]):
        model_type = KnowledgeGraph

    repository_type = Repo


class KnowledgeGraphSourceService(
    service.SQLAlchemyAsyncRepositoryService[KnowledgeGraphSource]
):
    async def list_sources(
        self, db_session: AsyncSession, graph_id: UUID
    ) -> list[KnowledgeGraphSourceExternalSchema]:
        result = await db_session.execute(
            select(KnowledgeGraphSource)
            .where(KnowledgeGraphSource.graph_id == graph_id)
            .order_by(KnowledgeGraphSource.created_at.desc())
        )
        sources = result.scalars().all()

        return [
            KnowledgeGraphSourceExternalSchema(
                id=str(source.id),
                name=source.name,
                type=source.type,
                config=source.config,
                status=source.status,
                documents_count=int(source.documents_count or 0),
                last_sync_at=source.last_sync_at,
                created_at=source.created_at.isoformat() if source.created_at else None,
            )
            for source in sources
        ]

    async def create_source(
        self,
        db_session: AsyncSession,
        graph_id: UUID,
        data: KnowledgeGraphSourceCreateRequest,
    ) -> KnowledgeGraphSourceCreateResponse:
        result = await db_session.execute(
            select(KnowledgeGraph).where(KnowledgeGraph.id == graph_id)
        )
        graph = result.scalar_one_or_none()
        if not graph:
            raise NotFoundException("Graph not found")

        source_type = (data.type or "").strip().lower()
        if not source_type:
            raise NotFoundException("Source type is required")

        provided_name = (data.name or "").strip()
        default_name = source_type.capitalize()
        source_name = provided_name or default_name

        created = await self.create(
            {
                "name": source_name,
                "type": source_type,
                "graph_id": graph_id,
                "config": data.config or {},
                "status": "not_synced",
                "documents_count": 0,
            }
        )

        return KnowledgeGraphSourceCreateResponse(
            id=str(created.id), name=created.name, type=created.type
        )

    async def update_source(
        self,
        db_session: AsyncSession,
        graph_id: UUID,
        source_id: UUID,
        data: KnowledgeGraphSourceUpdateRequest,
    ) -> KnowledgeGraphSourceExternalSchema:
        result = await db_session.execute(
            select(KnowledgeGraphSource).where(
                (KnowledgeGraphSource.id == source_id)
                & (KnowledgeGraphSource.graph_id == graph_id)
            )
        )
        source = result.scalar_one_or_none()
        if not source:
            raise NotFoundException("Source not found")

        if data.name is not None:
            source.name = data.name

        if data.status is not None:
            source.status = data.status

        if data.config is not None:
            current = source.config or {}
            # Shallow merge of provided keys into existing config
            merged = dict(current)
            merged.update(data.config or {})
            source.config = merged

        await db_session.commit()

        return KnowledgeGraphSourceExternalSchema(
            id=str(source.id),
            name=source.name,
            type=source.type,
            config=source.config,
            status=source.status,
            documents_count=int(source.documents_count or 0),
            last_sync_at=source.last_sync_at,
            created_at=source.created_at.isoformat() if source.created_at else None,
        )

    async def delete_source(
        self,
        db_session: AsyncSession,
        graph_id: UUID,
        source_id: UUID,
        cascade: bool = False,
    ) -> None:
        result = await db_session.execute(
            select(KnowledgeGraphSource).where(
                (KnowledgeGraphSource.id == source_id)
                & (KnowledgeGraphSource.graph_id == graph_id)
            )
        )
        source = result.scalar_one_or_none()
        if not source:
            raise NotFoundException("Source not found")

        # If cascade requested, delete all documents (and chunks via DB FK cascade) linked to this source
        if cascade:
            docs_table = docs_table_name(graph_id)
            ch_table = chunks_table_name(graph_id)

            # Explicitly delete chunks first (safer than relying solely on DB cascade)
            await db_session.execute(
                text(f"""
                    DELETE FROM {ch_table}
                    WHERE document_id IN (
                        SELECT id FROM {docs_table} WHERE source_id = :source_id
                    )
                """),
                {"source_id": str(source_id)},
            )

            await db_session.execute(
                text(f"DELETE FROM {docs_table} WHERE source_id = :source_id"),
                {"source_id": str(source_id)},
            )

        await db_session.delete(source)
        await db_session.commit()

    async def sync_source(
        self, db_session: AsyncSession, graph_id: UUID, source_id: UUID
    ) -> dict[str, Any]:
        result = await db_session.execute(
            select(KnowledgeGraphSource).where(
                (KnowledgeGraphSource.id == source_id)
                & (KnowledgeGraphSource.graph_id == graph_id)
            )
        )
        source = result.scalar_one_or_none()
        if not source:
            raise NotFoundException("Source not found")

        source.status = "syncing"
        await db_session.commit()

        try:
            if source.type == "sharepoint":
                summary = await SharePointDataSource().sync_source(db_session, source)
            else:
                raise NotFoundException(
                    f"Sync for source type '{source.type}' is not implemented"
                )

            # Type-specific sync should set final status; update last_sync_at for visibility
            source.last_sync_at = utc_now_isoformat()
            await db_session.commit()
            return summary
        except Exception as e:  # noqa: BLE001
            source.status = "failed"
            if hasattr(source, "status_message"):
                setattr(source, "status_message", str(e))
            await db_session.commit()
            raise ClientException(f"Sync failed: {e}")

    class Repo(repository.SQLAlchemyAsyncRepository[KnowledgeGraphSource]):
        model_type = KnowledgeGraphSource

    repository_type = Repo


class KnowledgeGraphDocumentService:
    async def list_documents(
        self, db_session: AsyncSession, graph_id: UUID
    ) -> list[KnowledgeGraphDocumentExternalSchema]:
        docs_table = docs_table_name(graph_id)
        ch_table = chunks_table_name(graph_id)
        rows = await db_session.execute(
            text(
                f"""
                SELECT
                    d.id::text AS id,
                    d.name AS name,
                    d.type AS type,
                    d.content_profile AS content_profile,
                    d.status AS status,
                    d.status_message AS status_message,
                    d.title AS title,
                    d.total_pages AS total_pages,
                    d.processing_time AS processing_time,
                    d.created_at AS created_at,
                    d.updated_at AS updated_at,
                    s.name AS source_name,
                    (SELECT COUNT(*) FROM {ch_table} c WHERE c.document_id = d.id) AS chunks_count
                FROM {docs_table} d
                LEFT JOIN knowledge_graph_sources s ON s.id = d.source_id
                ORDER BY d.created_at DESC
                """
            )
        )
        documents: list[KnowledgeGraphDocumentExternalSchema] = []
        for row in rows.fetchall():
            documents.append(
                KnowledgeGraphDocumentExternalSchema(
                    id=str(row.id),
                    name=row.name,
                    type=row.type,
                    content_profile=row.content_profile,
                    status=row.status,
                    status_message=row.status_message,
                    title=row.title,
                    total_pages=row.total_pages,
                    processing_time=row.processing_time,
                    chunks_count=int(row.chunks_count or 0),
                    source_name=row.source_name if row.source_name else None,
                    created_at=row.created_at.isoformat() if row.created_at else None,
                    updated_at=row.updated_at.isoformat() if row.updated_at else None,
                )
            )

        return documents

    async def get_document(
        self, db_session: AsyncSession, graph_id: UUID, document_id: UUID
    ) -> KnowledgeGraphDocumentDetailSchema:
        docs_table = docs_table_name(graph_id)
        ch_table = chunks_table_name(graph_id)
        res = await db_session.execute(
            text(
                f"""
                SELECT
                    d.id::text AS id,
                    d.name AS name,
                    d.type AS type,
                    d.content_profile AS content_profile,
                    d.title AS title,
                    d.summary AS summary,
                    d.toc AS toc,
                    d.status AS status,
                    d.status_message AS status_message,
                    d.total_pages AS total_pages,
                    d.processing_time AS processing_time,
                    d.created_at AS created_at,
                    d.updated_at AS updated_at,
                    (SELECT COUNT(*) FROM {ch_table} c WHERE c.document_id = d.id) AS chunks_count
                FROM {docs_table} d
                WHERE d.id = :id
                """
            ),
            {"id": str(document_id)},
        )
        row = res.one_or_none()
        if not row:
            raise NotFoundException("Document not found")

        return KnowledgeGraphDocumentDetailSchema(
            id=str(row.id),
            name=row.name,
            type=row.type,
            content_profile=row.content_profile,
            title=row.title,
            summary=row.summary,
            toc=row.toc,
            status=row.status,
            status_message=row.status_message,
            total_pages=row.total_pages,
            processing_time=row.processing_time,
            source_id=None,
            chunks_count=int(row.chunks_count or 0),
            created_at=row.created_at.isoformat() if row.created_at else None,
            updated_at=row.updated_at.isoformat() if row.updated_at else None,
        )

    async def delete_document(
        self, db_session: AsyncSession, graph_id: UUID, document_id: UUID
    ) -> None:
        docs_table = docs_table_name(graph_id)
        ch_table = chunks_table_name(graph_id)

        # Explicitly delete chunks first
        await db_session.execute(
            text(f"DELETE FROM {ch_table} WHERE document_id = :doc_id"),
            {"doc_id": str(document_id)},
        )

        res = await db_session.execute(
            text(f"DELETE FROM {docs_table} WHERE id = :id RETURNING 1"),
            {"id": str(document_id)},
        )
        deleted = res.scalar_one_or_none()
        await db_session.commit()
        if not deleted:
            raise NotFoundException("Document not found")


class KnowledgeGraphChunkService:
    async def list_chunks(
        self,
        db_session: AsyncSession,
        graph_id: UUID,
        limit: int = 50,
        offset: int = 0,
        q: str | None = None,
        document_id: UUID | None = None,
    ) -> KnowledgeGraphChunkListResponse:
        docs_table = docs_table_name(graph_id)
        ch_table = chunks_table_name(graph_id)

        where_clauses = []
        params: dict[str, Any] = {}
        if document_id is not None:
            where_clauses.append("c.document_id = :doc_id")
            params["doc_id"] = str(document_id)
        if q:
            where_clauses.append(
                "(c.title ILIKE :q OR c.name ILIKE :q OR c.text ILIKE :q)"
            )
            params["q"] = f"%{q}%"
        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        count_res = await db_session.execute(
            text(
                f"""
                SELECT COUNT(*) FROM {ch_table} c
                JOIN {docs_table} d ON d.id = c.document_id
                {where_sql}
                """
            ),
            params,
        )
        total_count = int(count_res.scalar() or 0)

        rows = await db_session.execute(
            text(
                f"""
                SELECT 
                    c.id::text AS id,
                    c.name AS name,
                    c.title AS title,
                    c.toc_reference AS toc_reference,
                    c.page AS page,
                    c.chunk_type AS chunk_type,
                    c.text AS text,
                    c.created_at AS created_at,
                    d.id::text AS document_id,
                    d.name AS document_name
                FROM {ch_table} c
                JOIN {docs_table} d ON d.id = c.document_id
                {where_sql}
                ORDER BY d.created_at DESC, c.page NULLS FIRST, c.created_at
                LIMIT :limit OFFSET :offset
                """
            ),
            {**params, "limit": int(limit), "offset": int(offset)},
        )
        rows_all = rows.fetchall()

        chunks: list[KnowledgeGraphChunkExternalSchema] = []
        for row in rows_all:
            chunks.append(
                KnowledgeGraphChunkExternalSchema(
                    id=str(row.id),
                    document_id=str(row.document_id),
                    document_name=row.document_name,
                    name=row.name,
                    title=row.title,
                    toc_reference=row.toc_reference,
                    page=row.page,
                    chunk_type=row.chunk_type,
                    text=row.text,
                    created_at=row.created_at.isoformat() if row.created_at else None,
                )
            )

        return KnowledgeGraphChunkListResponse(
            chunks=chunks, total=total_count, limit=limit, offset=offset
        )
