"""FlowProducer helpers for multi-step DAG pipelines.

Wraps ``asyncmq.flow.FlowProducer`` with convenience functions that build
``Job`` objects, wire up ``depends_on`` links, and route each step to the
correct queue.

Usage in application code::

    from scheduler.flows import run_sync_then_postprocess

    job_ids = await run_sync_then_postprocess(
        source_id="abc-123",
        params={...},
    )

Custom ad-hoc flows can be built with :func:`run_flow`.
"""

from __future__ import annotations

import uuid
from logging import getLogger
from typing import Any

from asyncmq.flow import FlowProducer
from asyncmq.jobs import Job

from scheduler.manager import get_backend
from scheduler.settings import QUEUE_SYNC

logger = getLogger(__name__)


# ---------------------------------------------------------------------------
# Low-level helper
# ---------------------------------------------------------------------------


def _task_id_for(func_name: str) -> str:
    """Build the fully-qualified task id that AsyncMQ registers for a function
    in :mod:`scheduler.executors`."""
    return f"scheduler.executors.{func_name}"


def _make_job_id(prefix: str | None = None) -> str:
    """Generate a unique job-id with an optional human-friendly prefix."""
    uid = uuid.uuid4().hex[:12]
    return f"{prefix}-{uid}" if prefix else uid


# ---------------------------------------------------------------------------
# Public: generic flow runner
# ---------------------------------------------------------------------------


async def run_flow(
    queue_name: str,
    jobs: list[Job],
) -> list[str]:
    """Enqueue an arbitrary DAG of :class:`Job` objects via ``FlowProducer``.

    Uses the PostgresBackend already initialised by :mod:`scheduler.manager`.

    Parameters
    ----------
    queue_name:
        Target queue.  All jobs in the flow are placed on this queue.
    jobs:
        Ordered list of ``Job`` instances.  Use ``depends_on`` to express
        edges in the DAG.

    Returns
    -------
    list[str]
        Job IDs in the order they were enqueued.
    """
    fp = FlowProducer(backend=get_backend())
    job_ids = await fp.add_flow(queue_name, jobs)
    logger.info(
        "Flow enqueued: queue=%s, jobs=%s",
        queue_name,
        job_ids,
    )
    return job_ids


# ---------------------------------------------------------------------------
# Pre-built pipeline: sync → post-process
# ---------------------------------------------------------------------------


async def run_sync_then_postprocess(
    *,
    source_id: str,
    job_definition: dict[str, Any] | None = None,
    sync_params: dict[str, Any] | None = None,
    postprocess_params: dict[str, Any] | None = None,
    job_id_prefix: str | None = None,
) -> list[str]:
    """Two-step DAG: sync a collection, then run post-processing.

    Steps
    ~~~~~
    1. ``execute_sync_collection``  → ``QUEUE_SYNC``
    2. ``execute_post_process_configuration``  → ``QUEUE_MAINTENANCE``
       (waits for step 1)

    Returns the list of enqueued job IDs ``[sync_id, postprocess_id]``.
    """
    prefix = job_id_prefix or source_id
    sync_id = _make_job_id(f"sync-{prefix}")
    pp_id = _make_job_id(f"pp-{prefix}")

    job_sync = Job(
        task_id=_task_id_for("execute_sync_collection"),
        args=[],
        kwargs={
            "job_id": sync_id,
            "job_definition": job_definition or {},
            "params": sync_params or {"source_id": source_id},
        },
        job_id=sync_id,
    )

    job_postprocess = Job(
        task_id=_task_id_for("execute_post_process_configuration"),
        args=[],
        kwargs={
            "job_id": pp_id,
            "job_definition": job_definition or {},
            "params": postprocess_params or {},
        },
        depends_on=[job_sync.id],
        job_id=pp_id,
    )

    return await run_flow(QUEUE_SYNC, [job_sync, job_postprocess])


# ---------------------------------------------------------------------------
# Pre-built pipeline: sync → evaluate
# ---------------------------------------------------------------------------


async def run_sync_then_evaluate(
    *,
    source_id: str,
    job_definition: dict[str, Any] | None = None,
    sync_params: dict[str, Any] | None = None,
    eval_params: dict[str, Any] | None = None,
    job_id_prefix: str | None = None,
) -> list[str]:
    """Two-step DAG: sync a collection, then evaluate it.

    Steps
    ~~~~~
    1. ``execute_sync_collection``  → ``QUEUE_SYNC``
    2. ``execute_evaluation``       → ``QUEUE_SYNC`` (same flow queue)
       (waits for step 1)
    """
    prefix = job_id_prefix or source_id
    sync_id = _make_job_id(f"sync-{prefix}")
    eval_id = _make_job_id(f"eval-{prefix}")

    job_sync = Job(
        task_id=_task_id_for("execute_sync_collection"),
        args=[],
        kwargs={
            "job_id": sync_id,
            "job_definition": job_definition or {},
            "params": sync_params or {"source_id": source_id},
        },
        job_id=sync_id,
    )

    job_eval = Job(
        task_id=_task_id_for("execute_evaluation"),
        args=[],
        kwargs={
            "job_id": eval_id,
            "job_definition": job_definition or {},
            "params": eval_params or {},
        },
        depends_on=[job_sync.id],
        job_id=eval_id,
    )

    return await run_flow(QUEUE_SYNC, [job_sync, job_eval])


# ---------------------------------------------------------------------------
# Pre-built pipeline: full sync → post-process + evaluate (diamond)
# ---------------------------------------------------------------------------


async def run_full_sync_pipeline(
    *,
    source_id: str,
    job_definition: dict[str, Any] | None = None,
    sync_params: dict[str, Any] | None = None,
    postprocess_params: dict[str, Any] | None = None,
    eval_params: dict[str, Any] | None = None,
    job_id_prefix: str | None = None,
) -> list[str]:
    """Diamond DAG: sync → (post-process AND evaluate) → cleanup.

    Steps
    ~~~~~
    1. ``execute_sync_collection`` — root
    2. ``execute_post_process_configuration`` — depends on (1)
    3. ``execute_evaluation``                 — depends on (1)
    4. ``execute_cleanup_logs``               — depends on (2) **and** (3)

    All jobs share a single queue so flow dependency tracking works
    correctly (AsyncMQ resolves deps within a queue).
    """
    prefix = job_id_prefix or source_id
    sync_id = _make_job_id(f"sync-{prefix}")
    pp_id = _make_job_id(f"pp-{prefix}")
    eval_id = _make_job_id(f"eval-{prefix}")
    cleanup_id = _make_job_id(f"clean-{prefix}")

    job_sync = Job(
        task_id=_task_id_for("execute_sync_collection"),
        args=[],
        kwargs={
            "job_id": sync_id,
            "job_definition": job_definition or {},
            "params": sync_params or {"source_id": source_id},
        },
        job_id=sync_id,
    )

    job_postprocess = Job(
        task_id=_task_id_for("execute_post_process_configuration"),
        args=[],
        kwargs={
            "job_id": pp_id,
            "job_definition": job_definition or {},
            "params": postprocess_params or {},
        },
        depends_on=[job_sync.id],
        job_id=pp_id,
    )

    job_eval = Job(
        task_id=_task_id_for("execute_evaluation"),
        args=[],
        kwargs={
            "job_id": eval_id,
            "job_definition": job_definition or {},
            "params": eval_params or {},
        },
        depends_on=[job_sync.id],
        job_id=eval_id,
    )

    job_cleanup = Job(
        task_id=_task_id_for("execute_cleanup_logs"),
        args=[],
        kwargs={
            "job_id": cleanup_id,
            "params": {},
        },
        depends_on=[job_postprocess.id, job_eval.id],
        job_id=cleanup_id,
    )

    return await run_flow(
        QUEUE_SYNC,
        [job_sync, job_postprocess, job_eval, job_cleanup],
    )
