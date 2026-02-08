import logging
import time
from typing import Any

from litestar import Controller, get, post
from litestar.params import Parameter
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from scheduler.flows import (
    run_flow,
    run_full_sync_pipeline,
    run_sync_then_evaluate,
    run_sync_then_postprocess,
)
from scheduler.job_executor import cancel_job, create_job
from scheduler.manager import get_backend, get_queue
from scheduler.settings import ALL_QUEUES, QUEUE_DEFAULT
from scheduler.types import JobDefinition, JobIdInput

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class FlowJobStep(BaseModel):
    """A single step in an ad-hoc flow."""

    task_id: str = Field(
        ...,
        description="Fully-qualified task id, e.g. scheduler.executors.execute_sync_collection",
    )
    args: list[Any] = Field(default_factory=list)
    kwargs: dict[str, Any] = Field(default_factory=dict)
    depends_on_indices: list[int] = Field(
        default_factory=list,
        description="0-based indices of steps this step depends on",
    )


class CreateFlowRequest(BaseModel):
    """Request body for ``POST /scheduler/create-flow``."""

    queue: str = Field(default=QUEUE_DEFAULT, description="Target queue for all steps")
    steps: list[FlowJobStep] = Field(..., min_length=1)


class CreatePipelineRequest(BaseModel):
    """Request body for named pipeline shortcuts."""

    pipeline: str = Field(
        ...,
        description="Pipeline name: sync_postprocess | sync_evaluate | full_sync",
    )
    source_id: str = Field(..., description="Data-source or collection ID")
    job_definition: dict[str, Any] | None = None
    sync_params: dict[str, Any] | None = None
    postprocess_params: dict[str, Any] | None = None
    eval_params: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _format_job(j: dict, state: str) -> dict:
    """Normalise a raw AsyncMQ job record into a consistent dict."""
    return {
        "id": j.get("id"),
        "task": j.get("task") or j.get("task_id"),
        "status": state,
        "args": j.get("args", []),
        "kwargs": j.get("kwargs", {}),
        "priority": j.get("priority", 0),
        "retries": j.get("retries", 0),
        "max_retries": j.get("max_retries", 0),
        "backoff": j.get("backoff"),
        "ttl": j.get("ttl"),
        "created_at": j.get("created_at"),
        "last_attempt": j.get("last_attempt"),
        "delay_until": j.get("delay_until"),
        "result": j.get("result"),
        "depends_on": j.get("depends_on", []),
        "repeat_every": j.get("repeat_every"),
    }


async def _list_all_jobs(queue) -> list[dict]:
    """Fetch jobs across every state."""
    jobs: list[dict] = []
    for state in ("waiting", "active", "completed", "failed", "delayed"):
        try:
            for j in await queue.list_jobs(state):
                jobs.append(_format_job(j, state))
        except Exception:
            pass
    return jobs


async def _get_status_counts(jobs: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for j in jobs:
        st = j.get("status", "unknown")
        counts[st] = counts.get(st, 0) + 1
    return counts


async def _get_repeatables(queue) -> list[dict]:
    repeatables: list[dict] = []
    try:
        for rep in await queue.list_repeatables():
            repeatables.append(
                {
                    "job_def": rep.job_def,
                    "next_run": rep.next_run,
                    "paused": rep.paused,
                }
            )
    except Exception:
        pass
    return repeatables


class SchedulerController(Controller):
    """Scheduler management endpoints.

    Job CRUD and multi-queue status API.  The full web-based dashboard
    is served by the built-in ``AsyncMQAdmin`` ASGI app mounted at
    ``/scheduler/dashboard``.
    """

    path = "/scheduler"
    tags = ["Admin / Scheduler"]

    # ------------------------------------------------------------------
    # Job management
    # ------------------------------------------------------------------

    @post("/create-job")
    async def create_job(
        self,
        data: JobDefinition,
        db_session: AsyncSession,
    ) -> dict:
        return await create_job(data, db_session)

    @post("/cancel-job")
    async def cancel_job(self, data: JobIdInput, db_session: AsyncSession) -> dict:
        return await cancel_job(data.job_id, db_session)

    # ------------------------------------------------------------------
    # Flow / Pipeline management
    # ------------------------------------------------------------------

    @post("/create-flow")
    async def create_flow(self, data: CreateFlowRequest) -> dict:
        """Enqueue an ad-hoc DAG of job steps via ``FlowProducer``.

        Each step references dependencies by their 0-based index in the
        ``steps`` list.  Returns the list of generated job IDs.
        """
        from asyncmq.jobs import Job

        jobs: list[Job] = []
        for idx, step in enumerate(data.steps):
            depends_on = [jobs[i].id for i in step.depends_on_indices if i < idx]
            job = Job(
                task_id=step.task_id,
                args=step.args,
                kwargs=step.kwargs,
                depends_on=depends_on or None,
            )
            jobs.append(job)

        job_ids = await run_flow(data.queue, jobs)
        return {"ok": True, "job_ids": job_ids}

    @post("/create-pipeline")
    async def create_pipeline(self, data: CreatePipelineRequest) -> dict:
        """Run a named pipeline shortcut (sync_postprocess, sync_evaluate,
        full_sync).  Builds the DAG internally and returns the job IDs."""

        common = dict(
            source_id=data.source_id,
            job_definition=data.job_definition,
            sync_params=data.sync_params,
        )

        match data.pipeline:
            case "sync_postprocess":
                ids = await run_sync_then_postprocess(
                    **common,
                    postprocess_params=data.postprocess_params,
                )
            case "sync_evaluate":
                ids = await run_sync_then_evaluate(
                    **common,
                    eval_params=data.eval_params,
                )
            case "full_sync":
                ids = await run_full_sync_pipeline(
                    **common,
                    postprocess_params=data.postprocess_params,
                    eval_params=data.eval_params,
                )
            case _:
                return {
                    "ok": False,
                    "error": f"Unknown pipeline '{data.pipeline}'. "
                    "Choose: sync_postprocess | sync_evaluate | full_sync",
                }

        return {"ok": True, "pipeline": data.pipeline, "job_ids": ids}

    # ------------------------------------------------------------------
    # Multi-queue status
    # ------------------------------------------------------------------

    @get("/queue-status")
    async def get_queue_status(
        self,
        queue_name: str | None = Parameter(query="queue", default=None),
    ) -> dict:
        """Get AsyncMQ queue information across all queues (or a specific one)."""

        backend = get_backend()
        now = time.time()
        queue_names = [queue_name] if queue_name else list(ALL_QUEUES)

        queues_data: list[dict] = []
        for qname in queue_names:
            try:
                q = get_queue(qname)
            except RuntimeError:
                continue

            stats = await q.queue_stats()
            is_paused = False
            try:
                is_paused = await backend.is_queue_paused(q.name)
            except Exception:
                pass

            jobs = await _list_all_jobs(q)
            repeatables = await _get_repeatables(q)
            status_counts = await _get_status_counts(jobs)

            queues_data.append(
                {
                    "queue": q.name,
                    "is_paused": is_paused,
                    "stats": stats,
                    "total_jobs": len(jobs),
                    "total_repeatables": len(repeatables),
                    "status_counts": status_counts,
                    "repeatables": repeatables,
                }
            )

        return {
            "server_time": now,
            "queues": queues_data,
        }

    # ------------------------------------------------------------------
    # Dashboard API – overview
    # ------------------------------------------------------------------

    @get("/overview")
    async def get_overview(
        self,
        queue_name: str | None = Parameter(query="queue", default=None),
    ) -> dict:
        """Aggregate overview for the dashboard header.

        When ``queue`` is omitted the response covers **all** queues.
        """
        backend = get_backend()
        now = time.time()
        queue_names = [queue_name] if queue_name else list(ALL_QUEUES)

        total_jobs = 0
        total_repeatables = 0
        status_counts: dict[str, int] = {}
        queue_summaries: list[dict] = []

        for qname in queue_names:
            try:
                q = get_queue(qname)
            except RuntimeError:
                continue

            jobs = await _list_all_jobs(q)
            repeatables = await _get_repeatables(q)
            counts = await _get_status_counts(jobs)

            is_paused = False
            try:
                is_paused = await backend.is_queue_paused(q.name)
            except Exception:
                pass

            for k, v in counts.items():
                status_counts[k] = status_counts.get(k, 0) + v

            total_jobs += len(jobs)
            total_repeatables += len(repeatables)

            queue_summaries.append(
                {
                    "queue": qname,
                    "is_paused": is_paused,
                    "total_jobs": len(jobs),
                    "total_repeatables": len(repeatables),
                    "status_counts": counts,
                }
            )

        return {
            "server_time": now,
            "queue": queue_name,
            "is_paused": queue_summaries[0]["is_paused"]
            if len(queue_summaries) == 1
            else False,
            "total_jobs": total_jobs,
            "total_repeatables": total_repeatables,
            "status_counts": status_counts,
            "queues": queue_summaries,
        }

    # ------------------------------------------------------------------
    # Dashboard API – jobs (paginated, filterable)
    # ------------------------------------------------------------------

    @get("/jobs")
    async def get_jobs(
        self,
        queue_name: str | None = Parameter(query="queue", default=None),
        job_state: str = Parameter(query="state", default="all"),
        page: int = Parameter(query="page", default=1, ge=1),
        size: int = Parameter(query="size", default=50, ge=1, le=200),
    ) -> dict:
        """Return paginated jobs, optionally filtered by state and queue."""
        queue_names = [queue_name] if queue_name else list(ALL_QUEUES)
        all_jobs: list[dict] = []

        for qname in queue_names:
            try:
                q = get_queue(qname)
            except RuntimeError:
                continue

            if job_state == "all":
                jobs = await _list_all_jobs(q)
            else:
                jobs = []
                try:
                    for j in await q.list_jobs(job_state):
                        jobs.append(_format_job(j, job_state))
                except Exception:
                    pass

            # Tag each job with its queue name
            for j in jobs:
                j["queue"] = qname
            all_jobs.extend(jobs)

        # Sort newest first
        all_jobs.sort(key=lambda j: j.get("created_at") or 0, reverse=True)

        total = len(all_jobs)
        total_pages = max(1, (total + size - 1) // size)
        start = (page - 1) * size
        paged = all_jobs[start : start + size]

        return {
            "jobs": paged,
            "total": total,
            "page": page,
            "size": size,
            "total_pages": total_pages,
        }

    # ------------------------------------------------------------------
    # Dashboard API – repeatables
    # ------------------------------------------------------------------

    @get("/repeatables")
    async def get_repeatables(
        self,
        queue_name: str | None = Parameter(query="queue", default=None),
    ) -> dict:
        """Return repeatable jobs across queues."""
        queue_names = [queue_name] if queue_name else list(ALL_QUEUES)
        all_repeatables: list[dict] = []

        for qname in queue_names:
            try:
                q = get_queue(qname)
            except RuntimeError:
                continue
            reps = await _get_repeatables(q)
            for r in reps:
                r["queue"] = qname
            all_repeatables.extend(reps)

        return {"repeatables": all_repeatables, "total": len(all_repeatables)}

    # ------------------------------------------------------------------
    # Dashboard API – metrics
    # ------------------------------------------------------------------

    @get("/metrics")
    async def get_metrics(
        self,
        queue_name: str | None = Parameter(query="queue", default=None),
    ) -> dict:
        """Aggregate metrics (throughput, failures, retries)."""
        queue_names = [queue_name] if queue_name else list(ALL_QUEUES)
        counts: dict[str, int] = {
            "waiting": 0,
            "active": 0,
            "completed": 0,
            "failed": 0,
            "delayed": 0,
        }
        for qname in queue_names:
            try:
                q = get_queue(qname)
            except RuntimeError:
                continue
            for s in counts:
                try:
                    jobs = await q.list_jobs(s)
                    counts[s] += len(jobs)
                except Exception:
                    pass

        return {
            "throughput": counts["completed"],
            "failures": counts["failed"],
            "retries": counts["failed"],
            "avg_duration": None,
        }

    # ------------------------------------------------------------------
    # Dashboard API – DLQ (failed jobs)
    # ------------------------------------------------------------------

    @get("/dlq")
    async def get_dlq(
        self,
        queue_name: str | None = Parameter(query="queue", default=None),
        page: int = Parameter(query="page", default=1, ge=1),
        size: int = Parameter(query="size", default=50, ge=1, le=200),
    ) -> dict:
        """Return paginated failed (dead-letter) jobs."""
        queue_names = [queue_name] if queue_name else list(ALL_QUEUES)
        all_failed: list[dict] = []

        for qname in queue_names:
            try:
                q = get_queue(qname)
            except RuntimeError:
                continue
            try:
                for j in await q.list_jobs("failed"):
                    job = _format_job(j, "failed")
                    job["queue"] = qname
                    all_failed.append(job)
            except Exception:
                pass

        all_failed.sort(key=lambda j: j.get("created_at") or 0, reverse=True)
        total = len(all_failed)
        total_pages = max(1, (total + size - 1) // size)
        start = (page - 1) * size
        paged = all_failed[start : start + size]

        return {
            "jobs": paged,
            "total": total,
            "page": page,
            "size": size,
            "total_pages": total_pages,
        }

    # ------------------------------------------------------------------
    # Queue control (per-queue)
    # ------------------------------------------------------------------

    @post("/queue/pause")
    async def pause_queue(
        self,
        queue_name: str = Parameter(query="queue", default="default"),
    ) -> dict:
        """Pause a queue – workers stop picking new jobs."""
        q = get_queue(queue_name)
        try:
            await q.pause()
            return {"ok": True, "action": "pause", "queue": queue_name}
        except Exception as e:
            logger.exception("Failed to pause queue %s", queue_name)
            return {"ok": False, "error": str(e)}

    @post("/queue/resume")
    async def resume_queue(
        self,
        queue_name: str = Parameter(query="queue", default="default"),
    ) -> dict:
        """Resume a paused queue."""
        q = get_queue(queue_name)
        try:
            await q.resume()
            return {"ok": True, "action": "resume", "queue": queue_name}
        except Exception as e:
            logger.exception("Failed to resume queue %s", queue_name)
            return {"ok": False, "error": str(e)}

    @post("/queue/clean")
    async def clean_queue(
        self,
        queue_name: str = Parameter(query="queue", default="default"),
        job_state: str = Parameter(query="state", default="completed"),
        older_than_hours: int = Parameter(query="older_than_hours", default=24),
    ) -> dict:
        """Purge jobs by state and age."""
        q = get_queue(queue_name)
        try:
            threshold = time.time() - (older_than_hours * 3600)
            await q.clean(job_state, older_than=threshold)
            return {
                "ok": True,
                "action": "clean",
                "queue": queue_name,
                "state": job_state,
                "older_than_hours": older_than_hours,
            }
        except Exception as e:
            logger.exception("Failed to clean queue %s", queue_name)
            return {"ok": False, "error": str(e)}

    # ------------------------------------------------------------------
    # Job actions (per-queue)
    # ------------------------------------------------------------------

    @post("/jobs/{job_id:str}/retry")
    async def retry_job(
        self,
        job_id: str,
        queue_name: str = Parameter(query="queue", default="default"),
    ) -> dict:
        """Retry a failed job."""
        q = get_queue(queue_name)
        backend = get_backend()
        try:
            await backend.retry_job(q.name, job_id)
            return {"ok": True, "action": "retry", "job_id": job_id}
        except Exception as e:
            logger.exception("Failed to retry job %s", job_id)
            return {"ok": False, "error": str(e)}

    @post("/jobs/{job_id:str}/remove")
    async def remove_job(
        self,
        job_id: str,
        queue_name: str = Parameter(query="queue", default="default"),
    ) -> dict:
        """Remove a job from a queue."""
        q = get_queue(queue_name)
        backend = get_backend()
        try:
            await backend.remove_job(q.name, job_id)
            return {"ok": True, "action": "remove", "job_id": job_id}
        except Exception as e:
            logger.exception("Failed to remove job %s", job_id)
            return {"ok": False, "error": str(e)}

    @post("/jobs/{job_id:str}/cancel")
    async def cancel_queue_job(
        self,
        job_id: str,
        queue_name: str = Parameter(query="queue", default="default"),
    ) -> dict:
        """Cancel a job in a specific queue."""
        q = get_queue(queue_name)
        try:
            await q.cancel_job(job_id)
            return {"ok": True, "action": "cancel", "job_id": job_id}
        except Exception as e:
            logger.exception("Failed to cancel job %s", job_id)
            return {"ok": False, "error": str(e)}
