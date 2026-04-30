"""Knowledge source + knowledge graph sync tasks."""

from __future__ import annotations

from logging import getLogger
from typing import Any
from uuid import UUID

from services.observability import observability_context, observe
from services.observability.models import FeatureType
from tasks.broker import broker
from tasks.status import with_job_status

logger = getLogger(__name__)


@broker.task(task_name="sync_collection", timeout=1800)
@with_job_status
@observe(name="Sync knowledge source", channel="Job")
async def sync_collection_task(
    *, job_id: str | None = None, system_name: str | None = None, **params: Any
) -> bool:
    """Sync a knowledge-source collection identified by its `system_name`.

    Used by user-scheduled recurring sync jobs.
    """
    # extra_data.params.system_name is the path the traces UI filters on
    # (see core/domain/traces/service.JsonbPathFilter._NESTED_PATHS). Keep
    # the structure in sync with what `execute_sync_collection` wrote under
    # APScheduler, otherwise the "Schedule & Runs" tab on a knowledge source
    # shows no runs.
    observability_context.update_current_trace(
        type=FeatureType.KNOWLEDGE_SOURCE.value,
        extra_data={
            "job_id": job_id,
            "params": {"system_name": system_name, **params},
        },
    )

    from routes.admin.knowledge_sources import sync_collection_standalone
    from services.utils.get_ids_by_system_names import get_ids_by_system_names

    if not system_name:
        raise ValueError(f"Missing system_name for job {job_id}")

    collection_id = await get_ids_by_system_names(system_name, "collections")
    if isinstance(collection_id, list):
        collection_id = collection_id[0] if collection_id else None

    if not collection_id:
        # Collection was deleted — cancel the schedule so it stops re-triggering.
        if job_id:
            from tasks import schedule_source
            from core.config.app import alchemy
            from core.domain.jobs.service import JobsService

            async with alchemy.get_session() as session:
                job = await JobsService(session=session).get_one_or_none(
                    id=UUID(job_id)
                )
                if job and job.taskiq_schedule_id:
                    try:
                        await schedule_source.delete_schedule(job.taskiq_schedule_id)
                    except Exception:  # noqa: BLE001
                        pass
        raise ValueError(
            f"Collection not found for system_name '{system_name}' in job {job_id}"
        )

    await sync_collection_standalone(collection_id)
    return True


@broker.task(task_name="sync_knowledge_graph_source", timeout=1800)
@with_job_status
@observe(name="Sync knowledge graph source", channel="Job")
async def sync_knowledge_graph_source_task(
    *,
    job_id: str | None = None,
    graph_id: str | None = None,
    source_id: str | None = None,
    **_: Any,
) -> bool:
    from core.config.app import alchemy
    from services.knowledge_graph.sources.sync_services import sync_source

    if not graph_id or not source_id:
        raise ValueError(f"Missing graph_id or source_id for job {job_id}")

    observability_context.update_current_trace(
        extra_data={
            "job_id": job_id,
            "params": {
                "graph_id": graph_id,
                "source_id": source_id,
                "system_name": str(graph_id),
            },
        },
    )

    async with alchemy.get_session() as session:
        await sync_source(session, UUID(str(graph_id)), UUID(str(source_id)))

    logger.info(
        "sync_knowledge_graph_source job %s: graph=%s source=%s",
        job_id,
        graph_id,
        source_id,
    )
    return True
