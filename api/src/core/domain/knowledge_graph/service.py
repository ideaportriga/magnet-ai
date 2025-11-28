from __future__ import annotations

from typing import Any
from uuid import UUID

from advanced_alchemy.extensions.litestar import repository, service
from litestar.exceptions import ClientException, NotFoundException
from litestar.status_codes import HTTP_415_UNSUPPORTED_MEDIA_TYPE
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models.knowledge_graph.knowledge_graph import KnowledgeGraph
from core.db.models.knowledge_graph.knowledge_graph_chunk import (
    KnowledgeGraphChunk,
)
from core.db.models.knowledge_graph.knowledge_graph_document import (
    KnowledgeGraphDocument,
)
from core.db.models.knowledge_graph.knowledge_graph_source import (
    KnowledgeGraphSource,
)
from core.domain.knowledge_graph.schemas import (
    KnowledgeGraphChunkExternalSchema,
    KnowledgeGraphChunkListResponse,
    KnowledgeGraphCreateRequest,
    KnowledgeGraphCreateResponse,
    KnowledgeGraphDocumentDetailSchema,
    KnowledgeGraphDocumentExternalSchema,
    KnowledgeGraphExternalSchema,
    KnowledgeGraphSourceCreateRequest,
    KnowledgeGraphSourceCreateResponse,
    KnowledgeGraphSourceExternalSchema,
    KnowledgeGraphSourceUpdateRequest,
    KnowledgeGraphUpdateRequest,
    KnowledgeGraphUpdateResponse,
)
from services.knowledge_graph import (
    get_content_config,
    get_default_content_configs,
    load_content_from_bytes,
)
from services.knowledge_graph.sources import (
    ManualUploadDataSource,
    SharePointDataSource,
)
from utils.datetime_utils import utc_now_isoformat


class KnowledgeGraphService(service.SQLAlchemyAsyncRepositoryService[KnowledgeGraph]):
    """Service for Knowledge Graph operations."""

    async def list_graphs(
        self, db_session: AsyncSession
    ) -> list[KnowledgeGraphExternalSchema]:
        result = await db_session.execute(
            select(
                KnowledgeGraph,
                func.count(func.distinct(KnowledgeGraphDocument.id)).label(
                    "documents_count"
                ),
                func.count(KnowledgeGraphChunk.id).label("chunks_count"),
            )
            .outerjoin(
                KnowledgeGraphDocument,
                KnowledgeGraphDocument.graph_id == KnowledgeGraph.id,
            )
            .outerjoin(
                KnowledgeGraphChunk,
                KnowledgeGraphChunk.document_id == KnowledgeGraphDocument.id,
            )
            .group_by(KnowledgeGraph.id)
            .order_by(KnowledgeGraph.created_at.desc())
        )

        rows = result.all()
        results: list[KnowledgeGraphExternalSchema] = []
        for row in rows:
            graph, documents_count, chunks_count = row
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
        result = await db_session.execute(
            select(
                KnowledgeGraph,
                func.count(func.distinct(KnowledgeGraphDocument.id)).label(
                    "documents_count"
                ),
                func.count(KnowledgeGraphChunk.id).label("chunks_count"),
            )
            .outerjoin(
                KnowledgeGraphDocument,
                KnowledgeGraphDocument.graph_id == KnowledgeGraph.id,
            )
            .outerjoin(
                KnowledgeGraphChunk,
                KnowledgeGraphChunk.document_id == KnowledgeGraphDocument.id,
            )
            .where(KnowledgeGraph.id == graph_id)
            .group_by(KnowledgeGraph.id)
        )

        row = result.one_or_none()
        if not row:
            raise NotFoundException("Graph not found")

        graph, documents_count, chunks_count = row
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
        self, data: KnowledgeGraphCreateRequest
    ) -> KnowledgeGraphCreateResponse:
        system_name = (
            (data.system_name or data.name)
            .upper()
            .replace(" ", "_")
            .replace(".", "_")
            .strip(" _")
        )

        default_configs = get_default_content_configs()
        settings: dict[str, Any] | None = {
            "chunking": {
                "content_settings": [cfg.model_dump() for cfg in default_configs],
            }
        }

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
            await db_session.execute(
                delete(KnowledgeGraphDocument).where(
                    (KnowledgeGraphDocument.graph_id == graph_id)
                    & (KnowledgeGraphDocument.source_id == source_id)
                )
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


class KnowledgeGraphDocumentService(
    service.SQLAlchemyAsyncRepositoryService[KnowledgeGraphDocument]
):
    async def list_documents(
        self, db_session: AsyncSession, graph_id: UUID
    ) -> list[KnowledgeGraphDocumentExternalSchema]:
        result = await db_session.execute(
            select(
                KnowledgeGraphDocument,
                KnowledgeGraphSource,
                func.count(KnowledgeGraphChunk.id).label("chunks_count"),
            )
            .outerjoin(
                KnowledgeGraphChunk,
                KnowledgeGraphChunk.document_id == KnowledgeGraphDocument.id,
            )
            .outerjoin(
                KnowledgeGraphSource,
                KnowledgeGraphSource.id == KnowledgeGraphDocument.source_id,
            )
            .where(KnowledgeGraphDocument.graph_id == graph_id)
            .group_by(KnowledgeGraphDocument.id, KnowledgeGraphSource.id)
            .order_by(KnowledgeGraphDocument.created_at.desc())
        )

        documents: list[KnowledgeGraphDocumentExternalSchema] = []
        for doc, source, chunks_count in result.all():
            documents.append(
                KnowledgeGraphDocumentExternalSchema(
                    id=str(doc.id),
                    name=doc.name,
                    type=doc.type,
                    content_profile=doc.content_profile,
                    status=doc.status,
                    status_message=getattr(doc, "status_message", None),
                    title=doc.title,
                    total_pages=doc.total_pages,
                    processing_time=getattr(doc, "processing_time", None),
                    chunks_count=int(chunks_count or 0),
                    source_name=source.name if source else None,
                    created_at=doc.created_at.isoformat() if doc.created_at else None,
                    updated_at=doc.updated_at.isoformat() if doc.updated_at else None,
                )
            )

        return documents

    async def get_document(
        self, db_session: AsyncSession, graph_id: UUID, document_id: UUID
    ) -> KnowledgeGraphDocumentDetailSchema:
        result = await db_session.execute(
            select(
                KnowledgeGraphDocument,
                func.count(KnowledgeGraphChunk.id).label("chunks_count"),
            )
            .outerjoin(
                KnowledgeGraphChunk,
                KnowledgeGraphDocument.id == KnowledgeGraphChunk.document_id,
            )
            .where(
                (KnowledgeGraphDocument.id == document_id)
                & (KnowledgeGraphDocument.graph_id == graph_id)
            )
            .group_by(KnowledgeGraphDocument.id)
        )

        row = result.one_or_none()
        if not row:
            raise NotFoundException("Document not found")

        doc, chunks_count = row
        return KnowledgeGraphDocumentDetailSchema(
            id=str(doc.id),
            name=doc.name,
            type=doc.type,
            content_profile=doc.content_profile,
            title=doc.title,
            summary=doc.summary,
            toc=doc.toc,
            status=doc.status,
            status_message=getattr(doc, "status_message", None),
            total_pages=doc.total_pages,
            processing_time=getattr(doc, "processing_time", None),
            source_id=str(doc.source_id) if getattr(doc, "source_id", None) else None,
            chunks_count=int(chunks_count or 0),
            created_at=doc.created_at.isoformat() if doc.created_at else None,
            updated_at=doc.updated_at.isoformat() if doc.updated_at else None,
        )

    async def delete_document(
        self, db_session: AsyncSession, graph_id: UUID, document_id: UUID
    ) -> None:
        result = await db_session.execute(
            select(KnowledgeGraphDocument).where(
                (KnowledgeGraphDocument.id == document_id)
                & (KnowledgeGraphDocument.graph_id == graph_id)
            )
        )
        document = result.scalar_one_or_none()
        if not document:
            raise NotFoundException("Document not found")

        await db_session.delete(document)
        await db_session.commit()

    class Repo(repository.SQLAlchemyAsyncRepository[KnowledgeGraphDocument]):
        model_type = KnowledgeGraphDocument

    repository_type = Repo


class KnowledgeGraphChunkService(
    service.SQLAlchemyAsyncRepositoryService[KnowledgeGraphChunk]
):
    async def list_chunks(
        self,
        db_session: AsyncSession,
        graph_id: UUID,
        limit: int = 50,
        offset: int = 0,
        q: str | None = None,
        document_id: UUID | None = None,
    ) -> KnowledgeGraphChunkListResponse:
        query = (
            select(KnowledgeGraphChunk, KnowledgeGraphDocument)
            .join(
                KnowledgeGraphDocument,
                KnowledgeGraphChunk.document_id == KnowledgeGraphDocument.id,
            )
            .where(KnowledgeGraphDocument.graph_id == graph_id)
        )

        if document_id is not None:
            query = query.where(KnowledgeGraphDocument.id == document_id)

        if q:
            search_pattern = f"%{q}%"
            query = query.where(
                (KnowledgeGraphChunk.title.ilike(search_pattern))
                | (KnowledgeGraphChunk.name.ilike(search_pattern))
                | (KnowledgeGraphChunk.text.ilike(search_pattern))
            )

        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db_session.execute(count_query)
        total_count = int(count_result.scalar() or 0)

        query = (
            query.order_by(
                KnowledgeGraphDocument.created_at.desc(),
                KnowledgeGraphChunk.page,
                KnowledgeGraphChunk.created_at,
            )
            .limit(limit)
            .offset(offset)
        )

        result = await db_session.execute(query)
        rows = result.all()

        chunks: list[KnowledgeGraphChunkExternalSchema] = []
        for chunk, document in rows:
            chunks.append(
                KnowledgeGraphChunkExternalSchema(
                    id=str(chunk.id),
                    document_id=str(document.id),
                    document_name=document.name,
                    name=chunk.name,
                    title=chunk.title,
                    toc_reference=getattr(chunk, "toc_reference", None),
                    page=getattr(chunk, "page", None),
                    chunk_type=getattr(chunk, "chunk_type", None),
                    text=getattr(chunk, "text", None),
                    created_at=chunk.created_at.isoformat()
                    if getattr(chunk, "created_at", None)
                    else None,
                )
            )

        return KnowledgeGraphChunkListResponse(
            chunks=chunks, total=total_count, limit=limit, offset=offset
        )

    class Repo(repository.SQLAlchemyAsyncRepository[KnowledgeGraphChunk]):
        model_type = KnowledgeGraphChunk

    repository_type = Repo
