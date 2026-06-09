from __future__ import annotations

from typing import Any
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
from services.knowledge_graph.content_config_services import (
    clone_graph_settings,
    ensure_fluid_topics_structured_profile,
    remove_auto_managed_fluid_topics_structured_profiles,
)
from services.knowledge_graph.models import SourceType
from core.domain.knowledge_graph.schemas import (
    KnowledgeGraphPhaseStatsSchema,
    KnowledgeGraphSourceCreateRequest,
    KnowledgeGraphSourceCreateResponse,
    KnowledgeGraphSourceExternalSchema,
    KnowledgeGraphSourceLastSyncSchema,
    KnowledgeGraphSourceScheduleExternalSchema,
    KnowledgeGraphSourceStatsSchema,
    KnowledgeGraphSourceSyncProgressSchema,
    KnowledgeGraphSourceUpdateRequest,
)


def _build_source_schema(
    *,
    source: KnowledgeGraphSource,
    schedule: KnowledgeGraphSourceScheduleExternalSchema | None,
    stats: KnowledgeGraphSourceStatsSchema | None,
) -> KnowledgeGraphSourceExternalSchema:
    """Build the external source schema, projecting JSONB columns into typed shapes.

    Centralizes the conversion so list + update endpoints stay in sync.
    """

    def _parse_jsonb_dict(value: Any) -> dict[str, Any] | None:
        if isinstance(value, dict):
            return value
        if isinstance(value, str) and value:
            try:
                import json as _json

                parsed = _json.loads(value)
                return parsed if isinstance(parsed, dict) else None
            except Exception:  # noqa: BLE001
                return None
        return None

    last_sync_raw = _parse_jsonb_dict(source.last_sync_stats)
    last_sync: KnowledgeGraphSourceLastSyncSchema | None = None
    if last_sync_raw is not None:
        try:
            last_sync = KnowledgeGraphSourceLastSyncSchema.model_validate(last_sync_raw)
        except Exception:  # noqa: BLE001
            last_sync = None

    sync_progress_raw = _parse_jsonb_dict(source.sync_progress)
    sync_progress: KnowledgeGraphSourceSyncProgressSchema | None = None
    if sync_progress_raw is not None:
        try:
            sync_progress = KnowledgeGraphSourceSyncProgressSchema.model_validate(
                sync_progress_raw
            )
        except Exception:  # noqa: BLE001
            sync_progress = None

    documents_count = stats.documents_count if stats else 0

    return KnowledgeGraphSourceExternalSchema(
        id=str(source.id),
        name=source.name,
        type=source.type,
        config=source.config,
        status=source.status,
        documents_count=documents_count,
        last_sync_at=source.last_sync_at,
        created_at=source.created_at.isoformat() if source.created_at else None,
        schedule=schedule,
        stats=stats,
        last_sync=last_sync,
        sync_progress=sync_progress,
    )


class KnowledgeGraphSourceService(
    service.SQLAlchemyAsyncRepositoryService[KnowledgeGraphSource]
):
    async def _has_sources_of_type(
        self, db_session: AsyncSession, *, graph_id: UUID, source_type: str
    ) -> bool:
        result = await db_session.execute(
            select(KnowledgeGraphSource.id)
            .where(KnowledgeGraphSource.graph_id == graph_id)
            .where(KnowledgeGraphSource.type == source_type)
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def _docs_table_exists(db_session: AsyncSession, docs_table: str) -> bool:
        """True if the per-graph docs table exists.

        Uses ``to_regclass`` which returns NULL instead of raising for a
        missing table, so the surrounding transaction is never aborted.
        """
        result = await db_session.execute(
            text("SELECT to_regclass(:t)"), {"t": docs_table}
        )
        return result.scalar_one() is not None

    async def _counts_by_source(
        self, db_session: AsyncSession, graph_id: UUID
    ) -> dict[str, int]:
        """Return the live document count per source for a graph.

        Computed on read from the per-graph docs table so we don't have to
        maintain a denormalized counter that drifts (and that breaks long
        syncs when the COUNT runs on an invalidated connection). Returns an
        empty dict if the docs table doesn't exist (e.g. graph has no
        embedding model configured yet).
        """
        docs_table = docs_table_name(graph_id)
        try:
            if not await self._docs_table_exists(db_session, docs_table):
                return {}
            # SAVEPOINT so an unexpected failure aborts only the nested
            # transaction: a session-level rollback would expire every ORM
            # object loaded in the session, and lazy re-loading them from
            # sync attribute access raises MissingGreenlet on async drivers.
            async with db_session.begin_nested():
                result = await db_session.execute(
                    text(
                        f"SELECT source_id::text, COUNT(*) FROM {docs_table} "
                        f"GROUP BY source_id"
                    )
                )
                return {row[0]: int(row[1]) for row in result.all()}
        except Exception:  # noqa: BLE001
            return {}

    async def _stats_by_source(
        self, db_session: AsyncSession, graph_id: UUID
    ) -> dict[str, KnowledgeGraphSourceStatsSchema]:
        """Aggregate per-phase document counts per source for a graph.

        One scan over the per-graph docs table produces all the counts the
        UI needs to render the pipeline strip on each source row. Same
        existence check and SAVEPOINT as ``_counts_by_source`` for graphs
        with no docs table yet.
        """
        docs_table = docs_table_name(graph_id)
        try:
            if not await self._docs_table_exists(db_session, docs_table):
                return {}
            # SAVEPOINT for the same reason as ``_counts_by_source``: a
            # session-level rollback would expire already-loaded ORM objects.
            async with db_session.begin_nested():
                result = await db_session.execute(
                    text(
                        f"""
                    SELECT
                        source_id::text AS source_id,
                        COUNT(*) AS documents_count,
                        COUNT(*) FILTER (WHERE status = 'completed') AS sync_completed,
                        COUNT(*) FILTER (WHERE status IN ('failed','error')) AS sync_failed,
                        COUNT(*) FILTER (WHERE status = 'processing') AS sync_running,
                        COUNT(*) FILTER (WHERE status = 'pending') AS sync_pending,
                        COUNT(*) FILTER (
                            WHERE pipeline_state->'metadata_extraction'->>'status' = 'completed'
                        ) AS metadata_completed,
                        COUNT(*) FILTER (
                            WHERE pipeline_state->'metadata_extraction'->>'status' = 'failed'
                        ) AS metadata_failed,
                        COUNT(*) FILTER (
                            WHERE pipeline_state->'metadata_extraction'->>'status' = 'running'
                        ) AS metadata_running,
                        COUNT(*) FILTER (
                            WHERE pipeline_state->'metadata_extraction'->>'status' = 'pending'
                        ) AS metadata_pending,
                        COUNT(*) FILTER (
                            WHERE pipeline_state->'entity_extraction'->>'status' = 'completed'
                        ) AS entity_completed,
                        COUNT(*) FILTER (
                            WHERE pipeline_state->'entity_extraction'->>'status' = 'failed'
                        ) AS entity_failed,
                        COUNT(*) FILTER (
                            WHERE pipeline_state->'entity_extraction'->>'status' = 'running'
                        ) AS entity_running,
                        COUNT(*) FILTER (
                            WHERE pipeline_state->'entity_extraction'->>'status' = 'pending'
                        ) AS entity_pending
                    FROM {docs_table}
                    GROUP BY source_id
                    """
                    )
                )
                rows = result.mappings().all()
            stats: dict[str, KnowledgeGraphSourceStatsSchema] = {}
            for row in rows:
                sid = str(row.get("source_id") or "")
                if not sid:
                    continue
                documents_count = int(row.get("documents_count") or 0)

                sync_completed = int(row.get("sync_completed") or 0)
                sync_failed = int(row.get("sync_failed") or 0)
                sync_running = int(row.get("sync_running") or 0)
                sync_pending = int(row.get("sync_pending") or 0)

                meta_completed = int(row.get("metadata_completed") or 0)
                meta_failed = int(row.get("metadata_failed") or 0)
                meta_running = int(row.get("metadata_running") or 0)
                meta_pending = int(row.get("metadata_pending") or 0)

                ent_completed = int(row.get("entity_completed") or 0)
                ent_failed = int(row.get("entity_failed") or 0)
                ent_running = int(row.get("entity_running") or 0)
                ent_pending = int(row.get("entity_pending") or 0)

                # ``total`` for sync covers every document (sync is always
                # attempted). For metadata/entities it only covers documents
                # the phase has actually touched, so the UI can show "not run"
                # for sources where extraction was never invoked.
                stats[sid] = KnowledgeGraphSourceStatsSchema(
                    documents_count=documents_count,
                    sync=KnowledgeGraphPhaseStatsSchema(
                        completed=sync_completed,
                        failed=sync_failed,
                        running=sync_running,
                        pending=sync_pending,
                        total=documents_count,
                    ),
                    metadata=KnowledgeGraphPhaseStatsSchema(
                        completed=meta_completed,
                        failed=meta_failed,
                        running=meta_running,
                        pending=meta_pending,
                        total=meta_completed
                        + meta_failed
                        + meta_running
                        + meta_pending,
                    ),
                    entities=KnowledgeGraphPhaseStatsSchema(
                        completed=ent_completed,
                        failed=ent_failed,
                        running=ent_running,
                        pending=ent_pending,
                        total=ent_completed + ent_failed + ent_running + ent_pending,
                    ),
                )
            return stats
        except Exception:  # noqa: BLE001
            return {}

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
        stats_by_source = await self._stats_by_source(db_session, graph_id)

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
            _build_source_schema(
                source=source,
                schedule=build_schedule(job),
                stats=stats_by_source.get(str(source.id)),
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
            }
        )

        if source_type == str(SourceType.FLUID_TOPICS):
            settings = clone_graph_settings(getattr(graph, "settings", None))
            if ensure_fluid_topics_structured_profile(settings):
                graph.settings = settings
                await db_session.commit()

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

        stats_by_source = await self._stats_by_source(db_session, graph_id)

        return _build_source_schema(
            source=source,
            schedule=None,
            stats=stats_by_source.get(str(source.id)),
        )

    async def delete_source(
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

        await self._delete_source_data(db_session, graph_id, source_id)
        await db_session.delete(source)
        await db_session.flush()

        if source.type == str(
            SourceType.FLUID_TOPICS
        ) and not await self._has_sources_of_type(
            db_session,
            graph_id=graph_id,
            source_type=str(SourceType.FLUID_TOPICS),
        ):
            graph_result = await db_session.execute(
                select(KnowledgeGraph).where(KnowledgeGraph.id == graph_id)
            )
            graph = graph_result.scalar_one_or_none()
            if graph:
                settings = clone_graph_settings(getattr(graph, "settings", None))
                if remove_auto_managed_fluid_topics_structured_profiles(settings):
                    graph.settings = settings

        await db_session.commit()

    async def purge_source_data(
        self,
        db_session: AsyncSession,
        graph_id: UUID,
        source_id: UUID,
    ) -> None:
        """Delete all documents and chunks for a source, keeping the source itself."""
        result = await db_session.execute(
            select(KnowledgeGraphSource).where(
                (KnowledgeGraphSource.id == source_id)
                & (KnowledgeGraphSource.graph_id == graph_id)
            )
        )
        source = result.scalar_one_or_none()
        if not source:
            raise NotFoundException("Source not found")

        await self._delete_source_data(db_session, graph_id, source_id)
        await db_session.commit()

    async def _delete_source_data(
        self,
        db_session: AsyncSession,
        graph_id: UUID,
        source_id: UUID,
    ) -> None:
        """Delete all documents and chunks for a source, keeping the source itself."""
        docs_table = docs_table_name(graph_id)
        ch_table = chunks_table_name(graph_id)

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

    class Repo(repository.SQLAlchemyAsyncRepository[KnowledgeGraphSource]):
        model_type = KnowledgeGraphSource

    repository_type = Repo
