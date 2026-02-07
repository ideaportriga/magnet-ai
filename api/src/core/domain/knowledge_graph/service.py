from __future__ import annotations

from typing import Any
from uuid import UUID

from advanced_alchemy.extensions.litestar import repository, service
from litestar.exceptions import ClientException, NotFoundException
from sqlalchemy import (
    Float,
    Index,
    MetaData,
    bindparam,
    delete,
    func,
    insert,
    or_,
    select,
    text,
    type_coerce,
    update,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.db.models.job import Job as JobModel
from core.db.models.knowledge_graph import (
    KnowledgeGraph,
    KnowledgeGraphChunk,
    KnowledgeGraphDocument,
    KnowledgeGraphMetadataDiscovery,
    KnowledgeGraphMetadataExtraction,
    KnowledgeGraphSource,
    chunks_index_prefix,
    chunks_table_name,
    docs_index_prefix,
    docs_table_name,
    knowledge_graph_chunk_table,
    knowledge_graph_document_table,
    resolve_vector_size_for_embedding_model,
)
from core.domain.ai_models.service import AIModelsService
from core.domain.knowledge_graph.schemas import (
    KnowledgeGraphChunkExternalSchema,
    KnowledgeGraphChunkListResponse,
    KnowledgeGraphCreateRequest,
    KnowledgeGraphCreateResponse,
    KnowledgeGraphDiscoveredMetadataExternalSchema,
    KnowledgeGraphDocumentDetailSchema,
    KnowledgeGraphDocumentExternalSchema,
    KnowledgeGraphExternalSchema,
    KnowledgeGraphExtractedMetadataExternalSchema,
    KnowledgeGraphExtractedMetadataUpsertRequest,
    KnowledgeGraphMetadataExtractionRunRequest,
    KnowledgeGraphMetadataExtractionRunResponse,
    KnowledgeGraphSourceCreateRequest,
    KnowledgeGraphSourceCreateResponse,
    KnowledgeGraphSourceExternalSchema,
    KnowledgeGraphSourceLinkExternalSchema,
    KnowledgeGraphSourceScheduleExternalSchema,
    KnowledgeGraphSourceScheduleSyncRequest,
    KnowledgeGraphSourceUpdateRequest,
    KnowledgeGraphUpdateRequest,
    KnowledgeGraphUpdateResponse,
)
from scheduler.job_executor import cancel_job, create_job
from scheduler.types import (
    JobDefinition,
    JobType,
    RunConfiguration,
    RunConfigurationType,
)
from services.knowledge_graph import (
    get_default_content_configs,
    get_default_metadata_settings,
    get_default_retrieval_settings,
)
from services.observability import observability_context
from services.observability.models import FeatureType
from utils.datetime_utils import utc_now_isoformat

from .schemas import ChunkSearchResult


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
        self,
        db_session: AsyncSession,
        data: KnowledgeGraphCreateRequest,
        *,
        document_service: KnowledgeGraphDocumentService | None = None,
        chunk_service: KnowledgeGraphChunkService | None = None,
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
        metadata_settings = get_default_metadata_settings()
        settings: dict[str, Any] | None = {
            "chunking": {
                "content_settings": [cfg.model_dump() for cfg in default_configs],
            },
            **retrieval_settings,
            **metadata_settings,
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

        # Create per-graph tables only when an embedding model is configured.
        embedding_model = (
            ((settings or {}).get("indexing") or {}).get("embedding_model")
            if isinstance(settings, dict)
            else None
        )
        if isinstance(embedding_model, str) and embedding_model.strip():
            vector_size = await resolve_vector_size_for_embedding_model(embedding_model)
            doc_svc = document_service or KnowledgeGraphDocumentService()
            ch_svc = chunk_service or KnowledgeGraphChunkService()
            await doc_svc.create_table(
                db_session, graph_id=created.id, vector_size=vector_size
            )
            await ch_svc.create_table(
                db_session, graph_id=created.id, vector_size=vector_size
            )

        return KnowledgeGraphCreateResponse(id=str(created.id))

    async def update_graph(
        self,
        db_session: AsyncSession,
        graph_id: UUID,
        data: KnowledgeGraphUpdateRequest,
        *,
        document_service: KnowledgeGraphDocumentService | None = None,
        chunk_service: KnowledgeGraphChunkService | None = None,
    ) -> KnowledgeGraphUpdateResponse:
        existing = await self.repository.get(graph_id)
        prev_settings = getattr(existing, "settings", None) or {}
        prev_indexing = (
            prev_settings.get("indexing") if isinstance(prev_settings, dict) else None
        )
        prev_embedding_model = (
            (prev_indexing or {}).get("embedding_model")
            if isinstance(prev_indexing, dict)
            else None
        )

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

        # If embedding model is configured (and changed), ensure per-graph tables exist.
        new_settings = getattr(updated, "settings", None) or {}
        new_indexing = (
            new_settings.get("indexing") if isinstance(new_settings, dict) else None
        )
        new_embedding_model = (
            (new_indexing or {}).get("embedding_model")
            if isinstance(new_indexing, dict)
            else None
        )
        if (
            isinstance(new_embedding_model, str)
            and new_embedding_model.strip()
            and new_embedding_model != prev_embedding_model
        ):
            vector_size = await resolve_vector_size_for_embedding_model(
                new_embedding_model
            )
            doc_svc = document_service or KnowledgeGraphDocumentService()
            ch_svc = chunk_service or KnowledgeGraphChunkService()
            await doc_svc.create_table(
                db_session, graph_id=graph_id, vector_size=vector_size
            )
            await ch_svc.create_table(
                db_session, graph_id=graph_id, vector_size=vector_size
            )

        return KnowledgeGraphUpdateResponse(
            id=str(updated.id),
            name=updated.name,
            system_name=getattr(updated, "system_name", None),
            description=getattr(updated, "description", None),
        )

    async def delete_graph(
        self,
        db_session: AsyncSession,
        graph_id: UUID,
        *,
        document_service: KnowledgeGraphDocumentService | None = None,
        chunk_service: KnowledgeGraphChunkService | None = None,
    ) -> None:
        """Delete a graph and drop its per-graph tables."""

        # Drop dynamic tables (chunks first due to FK)
        doc_svc = document_service or KnowledgeGraphDocumentService()
        ch_svc = chunk_service or KnowledgeGraphChunkService()
        await ch_svc.drop_table(db_session, graph_id=graph_id)
        await doc_svc.drop_table(db_session, graph_id=graph_id)
        await db_session.commit()

        # Remove graph record
        await self.delete(item_id=graph_id, auto_commit=True)

    class Repo(repository.SQLAlchemyAsyncRepository[KnowledgeGraph]):
        model_type = KnowledgeGraph

    repository_type = Repo


class KnowledgeGraphSourceService(
    service.SQLAlchemyAsyncRepositoryService[KnowledgeGraphSource]
):
    async def set_source_status(
        self, db_session: AsyncSession, source_id: UUID, status: str
    ) -> None:
        """Update source status."""
        await db_session.execute(
            update(KnowledgeGraphSource)
            .where(KnowledgeGraphSource.id == source_id)
            .values(status=status)
        )

    async def list_sources(
        self, db_session: AsyncSession, graph_id: UUID
    ) -> list[KnowledgeGraphSourceExternalSchema]:
        result = await db_session.execute(
            select(KnowledgeGraphSource, JobModel)
            .outerjoin(JobModel, KnowledgeGraphSource.schedule_job_id == JobModel.id)
            .where(KnowledgeGraphSource.graph_id == graph_id)
            .order_by(KnowledgeGraphSource.created_at.desc())
        )
        rows = result.all()

        def build_schedule(
            job: JobModel | None,
        ) -> KnowledgeGraphSourceScheduleExternalSchema | None:
            if not job or not job.definition:
                return None
            definition = job.definition or {}
            return KnowledgeGraphSourceScheduleExternalSchema(
                name=definition.get("name"),
                interval=definition.get("interval"),
                cron=definition.get("cron"),
                timezone=definition.get("timezone"),
            )

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
                schedule=build_schedule(job),
            )
            for (source, job) in rows
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

    async def schedule_source_sync(
        self,
        db_session: AsyncSession,
        graph_id: UUID,
        source_id: UUID,
        data: KnowledgeGraphSourceScheduleSyncRequest | None = None,
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

        # "None" is a UI-only scheduling option to disable automatic sync.
        # When requested, remove any existing schedule and return an idempotent response.
        interval_raw = getattr(data, "interval", None) if data else None
        if isinstance(interval_raw, str) and interval_raw.strip().lower() == "none":
            if source.schedule_job_id:
                job_id = str(source.schedule_job_id)
                try:
                    await cancel_job(job_id, db_session)
                except Exception:  # noqa: BLE001
                    pass

                # NOTE: cancel_job() uses `async with db_session`, which closes the session and
                # detaches ORM instances. Merge it back into the session before updating.
                source_for_update = await db_session.merge(source)
                source_for_update.schedule_job_id = None
                await db_session.commit()
            return {"status": "unscheduled"}

        run_configuration = RunConfiguration(
            type=RunConfigurationType.SYNC_KNOWLEDGE_GRAPH_SOURCE,
            params={
                "graph_id": str(graph_id),
                "source_id": str(source_id),
                "system_name": str(graph_id),
            },
        )

        # Always use an auto-generated name (UI no longer allows custom schedule names).
        graph_res = await db_session.execute(
            select(KnowledgeGraph).where(KnowledgeGraph.id == graph_id),
        )
        graph = graph_res.scalar_one_or_none()
        graph_name = graph.name if graph else str(graph_id)
        schedule_name = f'Sync job for graph "{graph_name}" for source "{source.name}"'

        # Always schedule as a recurring job (hardcoded).
        # Client may provide interval/cron/name/timezone; job_type and run_configuration are enforced here.
        job_definition = JobDefinition(
            name=schedule_name,
            job_type=JobType.RECURRING,
            interval=((data.interval if data else None) or "daily"),
            cron=((data.cron if data else None) or {"minute": "0", "hour": "3"}),
            timezone=((data.timezone if data else None) or "UTC"),
            run_configuration=run_configuration,
        )

        # Reconfigure existing schedule instead of creating duplicates.
        # If a schedule already exists, we store its job id on the source for a cheap join.
        if source.schedule_job_id:
            job_definition = job_definition.model_copy(
                update={"job_id": str(source.schedule_job_id)}
            )

        job_result = await create_job(job_definition, db_session)

        # Persist schedule_job_id for stable joins in list_sources().
        job_id = job_result.get("job_id")
        if job_id:
            # NOTE: scheduler.create_job() currently uses `async with db_session`, which
            # closes the session and expunges ORM instances. That detaches `source`,
            # so assigning on it won't be flushed. Merge it back into the session.
            source_for_update = await db_session.merge(source)
            source_for_update.schedule_job_id = UUID(job_id)
            await db_session.commit()

        return job_result

    async def unschedule_source_sync(
        self,
        db_session: AsyncSession,
        graph_id: UUID,
        source_id: UUID,
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

        if not source.schedule_job_id:
            # Idempotent: already unscheduled
            return

        job_id = str(source.schedule_job_id)

        # Best-effort cancel: even if the job is missing, still clear the link on the source.
        try:
            await cancel_job(job_id, db_session)
        except Exception:  # noqa: BLE001
            pass

        source_for_update = await db_session.merge(source)
        source_for_update.schedule_job_id = None
        await db_session.commit()

    async def sync_source_background(self, graph_id: UUID, source_id: UUID) -> None:
        """Run sync in background with its own database session.

        This method is called via asyncio.create_task() and should not raise exceptions
        to the caller. All errors are logged and stored in the source status.
        """
        from core.config.app import alchemy

        try:
            async with alchemy.get_session() as db_session:
                await self._sync_source_impl(db_session, graph_id, source_id)
        except Exception as e:  # noqa: BLE001
            # Log the error but don't raise - this is running in background
            import logging

            logger = logging.getLogger(__name__)
            logger.error(
                f"Background sync failed for graph {graph_id} source {source_id}: {e}",
                exc_info=True,
            )

    async def sync_source(
        self, db_session: AsyncSession, graph_id: UUID, source_id: UUID
    ) -> dict[str, Any]:
        """Synchronous sync method (used by scheduled jobs)."""
        return await self._sync_source_impl(db_session, graph_id, source_id)

    async def _sync_source_impl(
        self, db_session: AsyncSession, graph_id: UUID, source_id: UUID
    ) -> dict[str, Any]:
        """Internal implementation of sync logic."""
        result = await db_session.execute(
            select(KnowledgeGraphSource, KnowledgeGraph)
            .join(KnowledgeGraph, KnowledgeGraphSource.graph_id == KnowledgeGraph.id)
            .where(
                (KnowledgeGraphSource.id == source_id)
                & (KnowledgeGraphSource.graph_id == graph_id)
            )
        )
        row = result.first()
        if not row:
            raise NotFoundException("Source not found")

        source, graph = row

        observability_context.update_current_trace(
            name=graph.name, type=FeatureType.KNOWLEDGE_GRAPH.value
        )

        source.status = "syncing"
        await db_session.commit()

        try:
            if source.type == "sharepoint":
                from services.knowledge_graph.sources import SharePointDataSource

                summary = await SharePointDataSource(source).sync_source(db_session)
            elif source.type == "fluid_topics":
                from services.knowledge_graph.sources import FluidTopicsSource

                summary = await FluidTopicsSource(source).sync_source(db_session)
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
    async def create_table(
        self, db_session: AsyncSession, *, graph_id: UUID, vector_size: int
    ) -> None:
        """Create the per-graph documents table + indexes if missing."""

        docs_name = docs_table_name(graph_id)
        index_prefix = docs_index_prefix(graph_id)
        conn = await db_session.connection(
            execution_options={"isolation_level": "AUTOCOMMIT"}
        )

        def _create(sync_conn) -> None:
            md = MetaData()
            docs_tbl = knowledge_graph_document_table(
                md, docs_name, vector_size=vector_size
            )
            docs_tbl.create(sync_conn, checkfirst=True)
            Index(f"{index_prefix}_name", docs_tbl.c.name).create(
                sync_conn, checkfirst=True
            )
            Index(f"{index_prefix}_source_id", docs_tbl.c.source_id).create(
                sync_conn, checkfirst=True
            )
            # Composite index for efficient sync queries by source + external document ID
            Index(
                f"{index_prefix}_source_doc_id",
                docs_tbl.c.source_id,
                docs_tbl.c.source_document_id,
            ).create(sync_conn, checkfirst=True)

        await conn.run_sync(_create)

    async def drop_table(self, db_session: AsyncSession, *, graph_id: UUID) -> None:
        """Drop the per-graph documents table if it exists.

        Note: chunks table must be dropped first due to FK.
        """

        docs_name = docs_table_name(graph_id)
        conn = await db_session.connection(
            execution_options={"isolation_level": "AUTOCOMMIT"}
        )

        def _drop(sync_conn) -> None:
            md = MetaData()
            docs_tbl = knowledge_graph_document_table(md, docs_name, vector_size=None)
            docs_tbl.drop(sync_conn, checkfirst=True)

        await conn.run_sync(_drop)

    async def list_documents(
        self, db_session: AsyncSession, graph_id: UUID
    ) -> list[KnowledgeGraphDocumentExternalSchema]:
        docs_table = docs_table_name(graph_id)
        ch_table = chunks_table_name(graph_id)

        md = MetaData()
        docs_tbl = knowledge_graph_document_table(md, docs_table, vector_size=None)
        chunks_tbl = knowledge_graph_chunk_table(
            md,
            ch_table,
            docs_table=docs_table,
            vector_size=None,
        )
        sources_tbl = KnowledgeGraphSource.__table__

        chunks_count_sq = (
            select(func.count())
            .select_from(chunks_tbl)
            .where(chunks_tbl.c.document_id == docs_tbl.c.id)
            .scalar_subquery()
        )

        stmt = (
            select(
                docs_tbl.c.id.label("id"),
                docs_tbl.c.name.label("name"),
                docs_tbl.c.type.label("type"),
                docs_tbl.c.content_profile.label("content_profile"),
                docs_tbl.c.status.label("status"),
                docs_tbl.c.status_message.label("status_message"),
                docs_tbl.c.title.label("title"),
                docs_tbl.c.total_pages.label("total_pages"),
                docs_tbl.c.processing_time.label("processing_time"),
                docs_tbl.c.created_at.label("created_at"),
                docs_tbl.c.updated_at.label("updated_at"),
                docs_tbl.c.external_link.label("external_link"),
                sources_tbl.c.name.label("source_name"),
                chunks_count_sq.label("chunks_count"),
            )
            .select_from(
                docs_tbl.outerjoin(
                    sources_tbl, sources_tbl.c.id == docs_tbl.c.source_id
                )
            )
            .order_by(docs_tbl.c.created_at.desc())
        )

        rows_all = (await db_session.execute(stmt)).mappings().all()
        documents: list[KnowledgeGraphDocumentExternalSchema] = []
        for row in rows_all:
            doc = KnowledgeGraphDocument.from_mapping(row)
            documents.append(
                KnowledgeGraphDocumentExternalSchema(
                    id=str(doc.id) if doc.id else "",
                    name=doc.name,
                    type=doc.type,
                    content_profile=doc.content_profile,
                    status=doc.status,
                    status_message=doc.status_message,
                    title=doc.title,
                    total_pages=doc.total_pages,
                    processing_time=doc.processing_time,
                    external_link=doc.external_link,
                    chunks_count=int(row.get("chunks_count") or 0),
                    source_name=(row.get("source_name") or None),
                    created_at=doc.created_at.isoformat() if doc.created_at else None,
                    updated_at=doc.updated_at.isoformat() if doc.updated_at else None,
                )
            )

        return documents

    async def get_document(
        self, db_session: AsyncSession, graph_id: UUID, document_id: UUID
    ) -> KnowledgeGraphDocumentDetailSchema:
        docs_table = docs_table_name(graph_id)
        ch_table = chunks_table_name(graph_id)

        md = MetaData()
        docs_tbl = knowledge_graph_document_table(md, docs_table, vector_size=None)
        chunks_tbl = knowledge_graph_chunk_table(
            md,
            ch_table,
            docs_table=docs_table,
            vector_size=None,
        )

        chunks_count_sq = (
            select(func.count())
            .select_from(chunks_tbl)
            .where(chunks_tbl.c.document_id == docs_tbl.c.id)
            .scalar_subquery()
        )

        stmt = (
            select(
                docs_tbl.c.id.label("id"),
                docs_tbl.c.name.label("name"),
                docs_tbl.c.type.label("type"),
                docs_tbl.c.content_profile.label("content_profile"),
                docs_tbl.c.title.label("title"),
                docs_tbl.c.summary.label("summary"),
                docs_tbl.c.toc.label("toc"),
                docs_tbl.c.metadata.label("metadata"),
                docs_tbl.c.status.label("status"),
                docs_tbl.c.status_message.label("status_message"),
                docs_tbl.c.total_pages.label("total_pages"),
                docs_tbl.c.processing_time.label("processing_time"),
                docs_tbl.c.external_link.label("external_link"),
                docs_tbl.c.created_at.label("created_at"),
                docs_tbl.c.updated_at.label("updated_at"),
                chunks_count_sq.label("chunks_count"),
            )
            .select_from(docs_tbl)
            .where(docs_tbl.c.id == document_id)
        )
        row = (await db_session.execute(stmt)).mappings().one_or_none()
        if not row:
            raise NotFoundException("Document not found")

        doc = KnowledgeGraphDocument.from_mapping(row)
        return KnowledgeGraphDocumentDetailSchema(
            id=str(doc.id) if doc.id else "",
            name=doc.name,
            type=doc.type,
            content_profile=doc.content_profile,
            title=doc.title,
            summary=doc.summary,
            toc=doc.toc,  # type: ignore[arg-type]
            status=doc.status,
            status_message=doc.status_message,
            total_pages=doc.total_pages,
            processing_time=doc.processing_time,
            external_link=doc.external_link,
            metadata=doc.metadata.to_dict() if doc.metadata else None,
            source_id=None,
            chunks_count=int(row.get("chunks_count") or 0),
            created_at=doc.created_at.isoformat() if doc.created_at else None,
            updated_at=doc.updated_at.isoformat() if doc.updated_at else None,
        )

    async def search_documents(
        self,
        db_session: AsyncSession,
        *,
        graph_id: UUID | str,
        query_vector: list[float],
        limit: int,
        min_score: float = 0.0,
        doc_filter_where_sql: str | None = None,
        doc_filter_where_params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Similarity search over per-graph documents using summary embeddings."""

        docs_table = docs_table_name(graph_id)
        md = MetaData()
        docs_tbl = knowledge_graph_document_table(md, docs_table, vector_size=None)

        # Alias for metadata filtering consistency (similar to chunk search)
        docs_alias = docs_tbl.alias("d")

        qvec = bindparam("qvec", type_=docs_alias.c.summary_embedding.type)
        distance_expr = docs_alias.c.summary_embedding.op("<=>")(qvec)
        score_expr = (1 - type_coerce(distance_expr, Float)).label("score")

        title_expr = func.coalesce(
            func.nullif(docs_alias.c.title, ""),
            docs_alias.c.name,
        ).label("title")

        stmt = (
            select(
                docs_alias.c.id.label("id"),
                title_expr,
                docs_alias.c.summary.label("summary"),
                score_expr,
            )
            .select_from(docs_alias)
            .where(docs_alias.c.summary_embedding.is_not(None))
            .order_by(score_expr.desc())
            .limit(int(limit))
        )

        if doc_filter_where_sql:
            stmt = stmt.where(text(str(doc_filter_where_sql)))

        exec_params: dict[str, Any] = {"qvec": query_vector}
        if isinstance(doc_filter_where_params, dict) and doc_filter_where_params:
            exec_params.update(doc_filter_where_params)

        rows = (await db_session.execute(stmt, exec_params)).mappings().all()

        return [
            {
                "id": str(r.get("id") or ""),
                "title": r.get("title"),
                "content": r.get("summary"),
                "score": float(r["score"]) if r.get("score") is not None else 0.0,
            }
            for r in rows
            if float(r.get("score") or 0.0) >= min_score
        ]

    async def update_document(
        self,
        db_session: AsyncSession,
        *,
        graph_id: UUID | str,
        document_id: UUID | str,
        fields: dict[str, Any],
        touch_updated_at: bool = True,
        auto_commit: bool = True,
        raise_if_missing: bool = False,
    ) -> bool:
        md = MetaData()
        docs_tbl = knowledge_graph_document_table(
            md, docs_table_name(graph_id), vector_size=None
        )

        allowed_cols = set(docs_tbl.c.keys())
        immutable_cols = {"id", "created_at"}

        requested_cols = set(fields.keys())
        unknown_cols = requested_cols - allowed_cols
        forbidden_cols = requested_cols & immutable_cols
        if unknown_cols or forbidden_cols:
            bad = sorted(unknown_cols | forbidden_cols)
            raise ValueError(f"Cannot update document fields: {', '.join(bad)}")

        update_values: dict[str, Any] = dict(fields)
        if touch_updated_at and "updated_at" not in update_values:
            update_values["updated_at"] = text("CURRENT_TIMESTAMP")

        # Guard against accidental no-ops (e.g. only touching updated_at).
        if not {k for k in update_values.keys() if k != "updated_at"}:
            return False

        doc_uuid: UUID = (
            document_id if isinstance(document_id, UUID) else UUID(str(document_id))
        )

        stmt = (
            update(docs_tbl)
            .where(docs_tbl.c.id == doc_uuid)
            .values(**update_values)
            .returning(docs_tbl.c.id)
        )

        try:
            res = await db_session.execute(stmt)
            updated_id = res.scalar_one_or_none()
            if auto_commit:
                await db_session.commit()
        except Exception:
            if auto_commit:
                # Keep session usable for best-effort callers.
                try:
                    await db_session.rollback()
                except Exception:  # noqa: BLE001
                    pass
            raise

        if updated_id is None and raise_if_missing:
            raise NotFoundException("Document not found")

        return updated_id is not None

    async def delete_document(
        self, db_session: AsyncSession, graph_id: UUID, id: UUID
    ) -> None:
        docs_table = docs_table_name(graph_id)
        ch_table = chunks_table_name(graph_id)

        md = MetaData()
        docs_tbl = knowledge_graph_document_table(md, docs_table, vector_size=None)
        chunks_tbl = knowledge_graph_chunk_table(
            md,
            ch_table,
            docs_table=docs_table,
            vector_size=None,
        )

        # Explicitly delete chunks first
        await db_session.execute(
            delete(chunks_tbl).where(chunks_tbl.c.document_id == id)
        )

        # Then delete the document row
        res = await db_session.execute(
            delete(docs_tbl).where(docs_tbl.c.id == id).returning(1)
        )
        deleted = res.scalar_one_or_none()
        await db_session.commit()
        if not deleted:
            raise NotFoundException("Document not found")


class KnowledgeGraphChunkService:
    async def create_table(
        self, db_session: AsyncSession, *, graph_id: UUID, vector_size: int
    ) -> None:
        """Create the per-graph chunks table + indexes if missing.

        Note: documents table must exist first due to FK.
        """

        docs_name = docs_table_name(graph_id)
        chunks_name = chunks_table_name(graph_id)
        index_prefix = chunks_index_prefix(graph_id)
        conn = await db_session.connection(
            execution_options={"isolation_level": "AUTOCOMMIT"}
        )

        def _create(sync_conn) -> None:
            md = MetaData()
            knowledge_graph_document_table(md, docs_name, vector_size=None)
            chunks_tbl = knowledge_graph_chunk_table(
                md, chunks_name, docs_table=docs_name, vector_size=vector_size
            )
            chunks_tbl.create(sync_conn, checkfirst=True)
            Index(f"{index_prefix}_document_id", chunks_tbl.c.document_id).create(
                sync_conn, checkfirst=True
            )

        await conn.run_sync(_create)

    async def drop_table(self, db_session: AsyncSession, *, graph_id: UUID) -> None:
        """Drop the per-graph chunks table if it exists."""

        docs_name = docs_table_name(graph_id)
        chunks_name = chunks_table_name(graph_id)
        conn = await db_session.connection(
            execution_options={"isolation_level": "AUTOCOMMIT"}
        )

        def _drop(sync_conn) -> None:
            md = MetaData()
            chunks_tbl = knowledge_graph_chunk_table(
                md, chunks_name, docs_table=docs_name, vector_size=None
            )
            chunks_tbl.drop(sync_conn, checkfirst=True)

        await conn.run_sync(_drop)

    async def insert_chunks_bulk(
        self,
        db_session: AsyncSession,
        *,
        graph_id: UUID | str,
        document: dict[str, Any],
        chunks: list[KnowledgeGraphChunk],
    ) -> int:
        """Insert chunks for a document into the per-graph chunks table.

        Notes:
        - Uses the caller-provided `db_session` and participates in the surrounding
          transaction (caller controls commit/rollback).
        - Chunks are `KnowledgeGraphChunk` objects; we persist their fields into the
          dynamic per-graph chunks table.
        - If `chunk.content_embedding` is missing/empty, we store NULL (chunk will not
          be returned by similarity search which filters on non-null embeddings).
        """

        if not chunks:
            return 0

        doc_id_raw = document.get("id")
        if not doc_id_raw:
            raise ValueError("document.id is required to insert chunks")
        doc_id: UUID = (
            doc_id_raw if isinstance(doc_id_raw, UUID) else UUID(str(doc_id_raw))
        )

        docs_tbl_name = docs_table_name(graph_id)
        chunks_tbl_name = chunks_table_name(graph_id)

        md = MetaData()
        chunks_tbl = knowledge_graph_chunk_table(
            md,
            chunks_tbl_name,
            docs_table=docs_tbl_name,
            vector_size=None,
        )

        document_name = str(document.get("name") or "")
        rows: list[dict[str, Any]] = []
        for idx, chunk in enumerate(chunks):
            # Some sources (e.g. Fluid Topics TOPIC chunks) do not have a page concept
            # and will pass `page=None`. `dict.get()` returns None even when a default
            # is provided if the key exists, so we normalize explicitly here.
            page_val = chunk.page
            page: int | None = (
                page_val if isinstance(page_val, int) and page_val > 0 else None
            )

            embedding_val = chunk.content_embedding
            embedding: list[float] | None = (
                embedding_val
                if isinstance(embedding_val, list) and len(embedding_val) > 0
                else None
            )

            chunk_type_val = chunk.chunk_type
            chunk_type = (
                str(chunk_type_val).strip() if chunk_type_val is not None else ""
            ) or "TEXT"

            rows.append(
                {
                    "name": f"{document_name}_chunk_{idx + 1}",
                    "index": idx,
                    "generated_id": chunk.generated_id,
                    "title": chunk.title or "",
                    "toc_reference": chunk.toc_reference or "",
                    "page": page,
                    "content": chunk.content or "",
                    "content_format": chunk.content_format,
                    "embedded_content": chunk.embedded_content or "",
                    "content_embedding": embedding,
                    "chunk_type": chunk_type,
                    "document_id": doc_id,
                }
            )

        if not rows:
            return 0

        await db_session.execute(insert(chunks_tbl), rows)
        return len(rows)

    async def search_chunks(
        self,
        db_session: AsyncSession,
        *,
        graph_id: UUID | str,
        query_vector: list[float],
        limit: int,
        only_doc_ids: list[str] | None = None,
        doc_filter_where_sql: str | None = None,
        doc_filter_where_params: dict[str, Any] | None = None,
    ) -> list[ChunkSearchResult]:
        """Similarity search over per-graph chunks."""

        docs_table = docs_table_name(graph_id)
        chunks_table = chunks_table_name(graph_id)

        md = MetaData()
        docs_tbl = knowledge_graph_document_table(md, docs_table, vector_size=None)
        chunks_tbl = knowledge_graph_chunk_table(
            md,
            chunks_table,
            docs_table=docs_table,
            vector_size=None,
        )
        # IMPORTANT: `findDocumentsByMetadata` compiles a raw SQL predicate that
        # references the documents table as alias `d` (e.g. `d.metadata ...`).
        # When reusing that predicate here, we must ensure the documents table is
        # present in the FROM clause with the same alias, otherwise Postgres will
        # raise "missing FROM-clause entry for table d".
        docs_alias = docs_tbl.alias("d")

        qvec = bindparam("qvec", type_=chunks_tbl.c.content_embedding.type)
        distance_expr = chunks_tbl.c.content_embedding.op("<=>")(qvec)
        score_expr = (1 - type_coerce(distance_expr, Float)).label("score")

        stmt = (
            select(
                chunks_tbl.c.id.label("id"),
                chunks_tbl.c.title.label("title"),
                chunks_tbl.c.content.label("content"),
                chunks_tbl.c.document_id.label("document_id"),
                docs_alias.c.name.label("document_name"),
                docs_alias.c.title.label("document_title"),
                chunks_tbl.c.page.label("page"),
                chunks_tbl.c.index.label("index"),
                score_expr,
            )
            .select_from(
                chunks_tbl.join(docs_alias, docs_alias.c.id == chunks_tbl.c.document_id)
            )
            .where(chunks_tbl.c.content_embedding.is_not(None))
            .order_by(score_expr.desc())
            .limit(int(limit))
        )

        if only_doc_ids:
            stmt = stmt.where(
                chunks_tbl.c.document_id.in_([UUID(str(x)) for x in only_doc_ids])
            )

        if doc_filter_where_sql:
            stmt = stmt.where(text(str(doc_filter_where_sql)))

        exec_params: dict[str, Any] = {"qvec": query_vector}
        if isinstance(doc_filter_where_params, dict) and doc_filter_where_params:
            exec_params.update(doc_filter_where_params)

        rows = (await db_session.execute(stmt, exec_params)).mappings().all()
        return [
            ChunkSearchResult(
                chunk=KnowledgeGraphChunk(
                    id=r["id"],
                    title=r.get("title"),
                    content=r.get("content"),
                    document_id=r.get("document_id"),
                    document=KnowledgeGraphDocument(
                        id=r.get("document_id"),
                        name=r.get("document_name"),
                        title=r.get("document_title"),
                    ),
                    page=r.get("page"),
                    index=r.get("index"),
                ),
                score=float(r["score"]) if r.get("score") is not None else None,
            )
            for r in rows
        ]

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

        md = MetaData()
        docs_tbl = knowledge_graph_document_table(md, docs_table, vector_size=None)
        chunks_tbl = knowledge_graph_chunk_table(
            md,
            ch_table,
            docs_table=docs_table,
            vector_size=None,
        )

        where_conditions = []
        if document_id is not None:
            where_conditions.append(chunks_tbl.c.document_id == document_id)
        if q:
            q_like = f"%{q}%"
            where_conditions.append(
                or_(
                    chunks_tbl.c.title.ilike(q_like),
                    chunks_tbl.c.name.ilike(q_like),
                    chunks_tbl.c.embedded_content.ilike(q_like),
                )
            )

        join_from = chunks_tbl.join(docs_tbl, docs_tbl.c.id == chunks_tbl.c.document_id)

        count_stmt = select(func.count()).select_from(join_from)
        if where_conditions:
            count_stmt = count_stmt.where(*where_conditions)
        total_count = int((await db_session.execute(count_stmt)).scalar() or 0)

        stmt = (
            select(
                chunks_tbl.c.id.label("id"),
                chunks_tbl.c.name.label("name"),
                chunks_tbl.c.title.label("title"),
                chunks_tbl.c.toc_reference.label("toc_reference"),
                chunks_tbl.c.page.label("page"),
                chunks_tbl.c.chunk_type.label("chunk_type"),
                chunks_tbl.c.content.label("content"),
                chunks_tbl.c.content_format.label("content_format"),
                chunks_tbl.c.created_at.label("created_at"),
                docs_tbl.c.id.label("document_id"),
                docs_tbl.c.name.label("document_name"),
            )
            .select_from(join_from)
            .order_by(
                docs_tbl.c.created_at.desc(),
                chunks_tbl.c.page.nullsfirst(),
                chunks_tbl.c.created_at,
            )
            .limit(int(limit))
            .offset(int(offset))
        )
        if where_conditions:
            stmt = stmt.where(*where_conditions)

        rows_all = (await db_session.execute(stmt)).mappings().all()

        chunks: list[KnowledgeGraphChunkExternalSchema] = []
        for row in rows_all:
            chunk = KnowledgeGraphChunk.from_mapping(row)
            chunks.append(
                KnowledgeGraphChunkExternalSchema(
                    id=str(chunk.id) if chunk.id else "",
                    document_id=str(row.get("document_id") or ""),
                    document_name=str(row.get("document_name") or ""),
                    name=chunk.name,
                    title=chunk.title,
                    toc_reference=chunk.toc_reference,
                    page=chunk.page,
                    chunk_type=chunk.chunk_type,
                    content=chunk.content,
                    content_format=chunk.content_format,
                    created_at=chunk.created_at.isoformat()
                    if chunk.created_at
                    else None,
                )
            )

        return KnowledgeGraphChunkListResponse(
            chunks=chunks, total=total_count, limit=limit, offset=offset
        )

    async def delete_chunks(
        self,
        db_session: AsyncSession,
        graph_id: UUID,
        *,
        document_id: UUID | None = None,
    ) -> None:
        md = MetaData()
        chunks_table = knowledge_graph_chunk_table(
            md,
            chunks_table_name(graph_id),
            docs_table=docs_table_name(graph_id),
            vector_size=None,
        )

        conditions = []
        if document_id is not None:
            conditions.append(chunks_table.c.document_id == document_id)

        await db_session.execute(delete(chunks_table).where(*conditions))
        await db_session.commit()


class KnowledgeGraphMetadataService:
    async def list_discovered_metadata(
        self, db_session: AsyncSession, graph_id: UUID
    ) -> list[KnowledgeGraphDiscoveredMetadataExternalSchema]:
        # Ensure the graph exists so we can distinguish "no fields yet" vs "graph not found".
        graph_res = await db_session.execute(
            select(KnowledgeGraph.id).where(KnowledgeGraph.id == graph_id)
        )
        if graph_res.scalar_one_or_none() is None:
            raise NotFoundException("Graph not found")

        res = await db_session.execute(
            select(KnowledgeGraphMetadataDiscovery)
            .where(KnowledgeGraphMetadataDiscovery.graph_id == graph_id)
            .where(KnowledgeGraphMetadataDiscovery.origin.in_(("file", "source")))
            .options(selectinload(KnowledgeGraphMetadataDiscovery.source))
            .order_by(
                KnowledgeGraphMetadataDiscovery.value_count.desc(),
                KnowledgeGraphMetadataDiscovery.name.asc(),
                KnowledgeGraphMetadataDiscovery.created_at.desc(),
            )
        )
        rows = res.scalars().all()

        return [
            KnowledgeGraphDiscoveredMetadataExternalSchema(
                id=str(row.id),
                name=row.name,
                inferred_type=row.inferred_type,
                origin=row.origin,
                sample_values=row.sample_values,
                value_count=int(row.value_count or 0),
                source=KnowledgeGraphSourceLinkExternalSchema(
                    id=str(row.source.id),
                    name=row.source.name,
                    type=row.source.type,
                )
                if row.source is not None
                else None,
                created_at=row.created_at.isoformat() if row.created_at else None,
                updated_at=row.updated_at.isoformat() if row.updated_at else None,
            )
            for row in rows
        ]

    async def list_extracted_metadata(
        self, db_session: AsyncSession, graph_id: UUID
    ) -> list[KnowledgeGraphExtractedMetadataExternalSchema]:
        # Ensure the graph exists so we can distinguish "no fields yet" vs "graph not found".
        graph_res = await db_session.execute(
            select(KnowledgeGraph.id).where(KnowledgeGraph.id == graph_id)
        )
        if graph_res.scalar_one_or_none() is None:
            raise NotFoundException("Graph not found")

        res = await db_session.execute(
            select(KnowledgeGraphMetadataExtraction)
            .where(KnowledgeGraphMetadataExtraction.graph_id == graph_id)
            .order_by(
                KnowledgeGraphMetadataExtraction.value_count.desc(),
                KnowledgeGraphMetadataExtraction.name.asc(),
                KnowledgeGraphMetadataExtraction.created_at.desc(),
            )
        )
        rows = res.scalars().all()

        out: list[KnowledgeGraphExtractedMetadataExternalSchema] = []
        for row in rows:
            settings = row.settings if isinstance(row.settings, dict) else {}
            allowed_values = settings.get("allowed_values")
            if not isinstance(allowed_values, list):
                allowed_values = None
            out.append(
                KnowledgeGraphExtractedMetadataExternalSchema(
                    id=str(row.id),
                    name=row.name,
                    value_type=str(settings.get("value_type") or "string"),
                    is_multiple=bool(settings.get("is_multiple")),
                    allowed_values=allowed_values,
                    llm_extraction_hint=str(settings.get("llm_extraction_hint") or "")
                    or None,
                    sample_values=row.sample_values,
                    value_count=int(row.value_count or 0),
                    created_at=row.created_at.isoformat() if row.created_at else None,
                    updated_at=row.updated_at.isoformat() if row.updated_at else None,
                )
            )
        return out

    async def upsert_extracted_metadata_field(
        self,
        db_session: AsyncSession,
        graph_id: UUID,
        data: KnowledgeGraphExtractedMetadataUpsertRequest,
    ) -> KnowledgeGraphExtractedMetadataExternalSchema:
        # Ensure graph exists
        graph_res = await db_session.execute(
            select(KnowledgeGraph.id).where(KnowledgeGraph.id == graph_id)
        )
        if graph_res.scalar_one_or_none() is None:
            raise NotFoundException("Graph not found")

        name = str(getattr(data, "name", "") or "").strip()
        if not name:
            raise ClientException("Field name is required")

        value_type = (
            str(getattr(data, "value_type", "") or "string").strip() or "string"
        )
        is_multiple = bool(getattr(data, "is_multiple", False))
        allowed_values = getattr(data, "allowed_values", None)
        if allowed_values is not None and not isinstance(allowed_values, list):
            allowed_values = None
        llm_extraction_hint = (
            str(getattr(data, "llm_extraction_hint", "") or "").strip() or None
        )

        settings: dict[str, Any] = {
            "value_type": value_type,
            "is_multiple": is_multiple,
        }
        if allowed_values is not None:
            settings["allowed_values"] = allowed_values
        if llm_extraction_hint:
            settings["llm_extraction_hint"] = llm_extraction_hint

        res = await db_session.execute(
            select(KnowledgeGraphMetadataExtraction).where(
                KnowledgeGraphMetadataExtraction.graph_id == graph_id,
                KnowledgeGraphMetadataExtraction.name == name,
            )
        )
        row = res.scalar_one_or_none()
        if row is None:
            row = KnowledgeGraphMetadataExtraction(
                graph_id=graph_id,
                name=name,
                settings=settings,
                sample_values=None,
                value_count=0,
            )
            db_session.add(row)
        else:
            row.settings = settings

        await db_session.commit()
        await db_session.refresh(row)

        allowed_values_out = settings.get("allowed_values")
        if not isinstance(allowed_values_out, list):
            allowed_values_out = None

        return KnowledgeGraphExtractedMetadataExternalSchema(
            id=str(row.id),
            name=row.name,
            value_type=str(settings.get("value_type") or "string"),
            is_multiple=bool(settings.get("is_multiple")),
            allowed_values=allowed_values_out,
            llm_extraction_hint=str(settings.get("llm_extraction_hint") or "") or None,
            sample_values=row.sample_values,
            value_count=int(row.value_count or 0),
            created_at=row.created_at.isoformat() if row.created_at else None,
            updated_at=row.updated_at.isoformat() if row.updated_at else None,
        )

    async def delete_extracted_metadata_field(
        self, db_session: AsyncSession, graph_id: UUID, name: str
    ) -> None:
        graph_res = await db_session.execute(
            select(KnowledgeGraph.id).where(KnowledgeGraph.id == graph_id)
        )
        if graph_res.scalar_one_or_none() is None:
            raise NotFoundException("Graph not found")

        fname = str(name or "").strip()
        if not fname:
            raise ClientException("Field name is required")

        res = await db_session.execute(
            select(KnowledgeGraphMetadataExtraction).where(
                KnowledgeGraphMetadataExtraction.graph_id == graph_id,
                KnowledgeGraphMetadataExtraction.name == fname,
            )
        )
        row = res.scalar_one_or_none()
        if row is None:
            return

        await db_session.delete(row)
        await db_session.commit()

    async def run_metadata_extraction(
        self,
        db_session: AsyncSession,
        graph_id: UUID,
        data: KnowledgeGraphMetadataExtractionRunRequest,
    ) -> KnowledgeGraphMetadataExtractionRunResponse:
        """Trigger LLM-based metadata extraction for all documents/chunks in a graph.

        This endpoint is intentionally best-effort and may take time for large graphs.
        """
        graph_res = await db_session.execute(
            select(KnowledgeGraph).where(KnowledgeGraph.id == graph_id)
        )
        graph = graph_res.scalar_one_or_none()
        if not graph:
            raise NotFoundException("Graph not found")

        settings = getattr(graph, "settings", None) or {}
        metadata_settings = (
            settings.get("metadata") if isinstance(settings, dict) else {}
        )
        extraction_settings = (
            metadata_settings.get("extraction")
            if isinstance(metadata_settings, dict)
            else {}
        ) or {}

        # Determine approach (prefer request; fall back to persisted settings)
        approach_raw = (
            str(data.approach).strip()
            if getattr(data, "approach", None) is not None
            else str(extraction_settings.get("approach") or "").strip()
        )
        if approach_raw not in ("chunks", "document"):
            raise ClientException("Extraction approach must be 'chunks' or 'document'")

        prompt_template_system_name = (
            str(data.prompt_template_system_name).strip()
            if getattr(data, "prompt_template_system_name", None) is not None
            else str(
                extraction_settings.get("prompt_template_system_name") or ""
            ).strip()
        )
        if not prompt_template_system_name:
            raise ClientException("Prompt template is required to run extraction")

        segment_size = (
            int(data.segment_size)
            if getattr(data, "segment_size", None) is not None
            else int(extraction_settings.get("segment_size") or 18000)
        )
        segment_overlap = (
            float(data.segment_overlap)
            if getattr(data, "segment_overlap", None) is not None
            else float(extraction_settings.get("segment_overlap") or 0.1)
        )

        # Import locally to avoid heavy imports / circular deps at module import time
        from services.knowledge_graph.llm_metadata_extraction import (
            build_typescript_schema_from_field_definitions,
            run_graph_llm_metadata_extraction,
        )

        # Schema + aggregation whitelist come strictly from DB-stored extraction fields.
        extracted_res = await db_session.execute(
            select(KnowledgeGraphMetadataExtraction).where(
                KnowledgeGraphMetadataExtraction.graph_id == graph_id
            )
        )
        extracted_rows = extracted_res.scalars().all()
        if not extracted_rows:
            raise ClientException("No extracted metadata fields configured")

        extracted_defs: list[dict[str, Any]] = []
        extraction_field_settings: dict[str, dict[str, Any]] = {}
        for r in extracted_rows:
            settings = r.settings if isinstance(r.settings, dict) else {}
            extracted_defs.append({"name": r.name, **settings})
            extraction_field_settings[r.name] = settings

        schema_str = build_typescript_schema_from_field_definitions(extracted_defs)

        # Reset aggregated stats so the UI reflects the current extraction run.
        await db_session.execute(
            update(KnowledgeGraphMetadataExtraction)
            .where(KnowledgeGraphMetadataExtraction.graph_id == graph_id)
            .values(sample_values=None, value_count=0, updated_at=func.now())
        )
        await db_session.commit()

        result = await run_graph_llm_metadata_extraction(
            db_session,
            graph_id=graph_id,
            approach=approach_raw,  # type: ignore[arg-type]
            prompt_template_system_name=prompt_template_system_name,
            extraction_field_settings=extraction_field_settings,
            schema=schema_str,
            segment_size=segment_size,
            segment_overlap=segment_overlap,
        )

        return KnowledgeGraphMetadataExtractionRunResponse(status="ok", **result)
