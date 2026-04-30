"""Knowledge-graph source schedule management (TaskIQ-backed)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from litestar.exceptions import NotFoundException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tasks.admin_ops import cancel_job, create_or_update_job
from tasks.types import (
    JobDefinition,
    JobType,
    RunConfiguration,
    RunConfigurationType,
)

if TYPE_CHECKING:
    from core.domain.knowledge_graph.schemas import (
        KnowledgeGraphSourceScheduleSyncRequest,
    )


async def schedule_source_sync(
    db_session: AsyncSession,
    graph_id: UUID,
    source_id: UUID,
    data: "KnowledgeGraphSourceScheduleSyncRequest | None" = None,
) -> dict[str, Any]:
    from core.db.models.knowledge_graph import KnowledgeGraph, KnowledgeGraphSource

    result = await db_session.execute(
        select(KnowledgeGraphSource).where(
            (KnowledgeGraphSource.id == source_id)
            & (KnowledgeGraphSource.graph_id == graph_id)
        )
    )
    source = result.scalar_one_or_none()
    if not source:
        raise NotFoundException("Source not found")

    # UI "None" interval = disable automatic sync.
    interval_raw = getattr(data, "interval", None) if data else None
    if isinstance(interval_raw, str) and interval_raw.strip().lower() == "none":
        if source.schedule_job_id:
            try:
                await cancel_job(str(source.schedule_job_id), db_session)
            except Exception:  # noqa: BLE001
                pass

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

    graph_res = await db_session.execute(
        select(KnowledgeGraph).where(KnowledgeGraph.id == graph_id),
    )
    graph = graph_res.scalar_one_or_none()
    graph_name = graph.name if graph else str(graph_id)
    schedule_name = f'Sync job for graph "{graph_name}" for source "{source.name}"'

    job_definition = JobDefinition(
        name=schedule_name,
        job_type=JobType.RECURRING,
        interval=((data.interval if data else None) or "daily"),
        cron=((data.cron if data else None) or {"minute": "0", "hour": "3"}),
        timezone=((data.timezone if data else None) or "UTC"),
        run_configuration=run_configuration,
    )

    if source.schedule_job_id:
        job_definition = job_definition.model_copy(
            update={"job_id": str(source.schedule_job_id)}
        )

    job_result = await create_or_update_job(job_definition, db_session)

    job_id = job_result.get("job_id")
    if job_id:
        source_for_update = await db_session.merge(source)
        source_for_update.schedule_job_id = UUID(job_id)
        await db_session.commit()

    return job_result


async def unschedule_source_sync(
    db_session: AsyncSession,
    graph_id: UUID,
    source_id: UUID,
) -> None:
    from core.db.models.knowledge_graph import KnowledgeGraphSource

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
        return

    try:
        await cancel_job(str(source.schedule_job_id), db_session)
    except Exception:  # noqa: BLE001
        pass

    source_for_update = await db_session.merge(source)
    source_for_update.schedule_job_id = None
    await db_session.commit()
