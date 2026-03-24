from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from litestar.exceptions import NotFoundException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from scheduler.types import (
    JobDefinition,
    JobType,
    RunConfiguration,
    RunConfigurationType,
)

if TYPE_CHECKING:
    from core.db.models.knowledge_graph import KnowledgeGraph, KnowledgeGraphSource
    from core.domain.knowledge_graph.schemas import (
        KnowledgeGraphSourceScheduleSyncRequest,
    )


async def schedule_source_sync(
    db_session: AsyncSession,
    graph_id: UUID,
    source_id: UUID,
    scheduler: AsyncIOScheduler,
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

    from scheduler.job_executor import cancel_job, create_job

    # "None" is a UI-only scheduling option to disable automatic sync.
    # When requested, remove any existing schedule and return an idempotent response.
    interval_raw = getattr(data, "interval", None) if data else None
    if isinstance(interval_raw, str) and interval_raw.strip().lower() == "none":
        if source.schedule_job_id:
            job_id = str(source.schedule_job_id)
            try:
                await cancel_job(scheduler, job_id, db_session)
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

    job_result = await create_job(scheduler, job_definition, db_session)

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
    db_session: AsyncSession,
    graph_id: UUID,
    source_id: UUID,
    scheduler: AsyncIOScheduler,
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

    from scheduler.job_executor import cancel_job

    # Best-effort cancel: even if the job is missing, still clear the link on the source.
    try:
        await cancel_job(scheduler, job_id, db_session)
    except Exception:  # noqa: BLE001
        pass

    source_for_update = await db_session.merge(source)
    source_for_update.schedule_job_id = None
    await db_session.commit()
