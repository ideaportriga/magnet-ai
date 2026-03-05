from __future__ import annotations

from uuid import UUID

from advanced_alchemy.extensions.litestar import repository, service
from litestar.exceptions import NotFoundException
from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models.job import Job as JobModel
from core.db.models.knowledge_graph import (
    KnowledgeGraph,
    KnowledgeGraphSource,
    chunks_table_name,
    docs_table_name,
)
from core.domain.knowledge_graph.schemas import (
    KnowledgeGraphSourceCreateRequest,
    KnowledgeGraphSourceCreateResponse,
    KnowledgeGraphSourceExternalSchema,
    KnowledgeGraphSourceScheduleExternalSchema,
    KnowledgeGraphSourceUpdateRequest,
)


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

    class Repo(repository.SQLAlchemyAsyncRepository[KnowledgeGraphSource]):
        model_type = KnowledgeGraphSource

    repository_type = Repo
