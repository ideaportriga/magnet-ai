import logging
import time

from litestar import Controller, get, post
from litestar.params import Parameter
from sqlalchemy.ext.asyncio import AsyncSession

from scheduler.job_executor import cancel_job, create_job
from scheduler.manager import get_backend, get_queue
from scheduler.types import JobDefinition, JobIdInput

logger = logging.getLogger(__name__)


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


async def _get_workers(backend, queue_name: str) -> list[dict]:
    workers: list[dict] = []
    try:
        for w in await backend.list_workers(queue_name):
            workers.append(
                {
                    "id": w.id,
                    "queue": w.queue,
                    "concurrency": w.concurrency,
                    "heartbeat": w.heartbeat,
                }
            )
    except Exception:
        pass
    return workers


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
    # Queue status  (legacy — returns everything in one call)
    # ------------------------------------------------------------------

    @get("/queue-status")
    async def get_queue_status(self) -> dict:
        """Get current AsyncMQ queue information including stats, jobs, repeatables and workers."""
        queue = get_queue()
        backend = get_backend()
        now = time.time()

        stats = await queue.queue_stats()

        is_paused = False
        try:
            is_paused = await backend.is_queue_paused(queue.name)
        except Exception:
            pass

        jobs = await _list_all_jobs(queue)
        repeatables = await _get_repeatables(queue)
        workers = await _get_workers(backend, queue.name)

        # Delayed jobs detail
        delayed_jobs: list[dict] = []
        try:
            for d in await backend.list_delayed(queue.name):
                delayed_jobs.append(
                    {"job_id": d.job_id, "run_at": d.run_at, "payload": d.payload}
                )
        except Exception:
            pass

        # Stalled jobs (heartbeat older than 60s)
        stalled_jobs: list[dict] = []
        try:
            for s in await backend.fetch_stalled_jobs(older_than=60.0):
                stalled_jobs.append(
                    {"queue": s.get("queue"), "job_data": s.get("job_data")}
                )
        except Exception:
            pass

        status_counts = await _get_status_counts(jobs)

        return {
            "queue": queue.name,
            "is_paused": is_paused,
            "server_time": now,
            "stats": stats,
            "jobs": jobs,
            "repeatables": repeatables,
            "workers": workers,
            "delayed_jobs": delayed_jobs,
            "stalled_jobs": stalled_jobs,
            "status_counts": status_counts,
        }

    # ------------------------------------------------------------------
    # Dashboard overview
    # ------------------------------------------------------------------

    @get("/dashboard/overview")
    async def get_dashboard_overview(self) -> dict:
        """Overview metrics: total queues, jobs, workers, job distribution."""
        queue = get_queue()
        backend = get_backend()
        now = time.time()

        is_paused = False
        try:
            is_paused = await backend.is_queue_paused(queue.name)
        except Exception:
            pass

        jobs = await _list_all_jobs(queue)
        status_counts = await _get_status_counts(jobs)
        workers = await _get_workers(backend, queue.name)
        repeatables = await _get_repeatables(queue)

        # Stalled jobs
        stalled_jobs: list[dict] = []
        try:
            for s in await backend.fetch_stalled_jobs(older_than=60.0):
                stalled_jobs.append(
                    {"queue": s.get("queue"), "job_data": s.get("job_data")}
                )
        except Exception:
            pass

        return {
            "queue": queue.name,
            "is_paused": is_paused,
            "server_time": now,
            "total_jobs": len(jobs),
            "total_workers": len(workers),
            "total_repeatables": len(repeatables),
            "total_stalled": len(stalled_jobs),
            "status_counts": status_counts,
            "workers": workers,
            "stalled_jobs": stalled_jobs,
        }

    # ------------------------------------------------------------------
    # Jobs (paginated, filtered by state)
    # ------------------------------------------------------------------

    @get("/dashboard/jobs")
    async def get_dashboard_jobs(
        self,
        job_state: str = Parameter(query="state", default="all"),
        page: int = Parameter(query="page", default=1),
        size: int = Parameter(query="size", default=50),
    ) -> dict:
        """Paginated job list with state filter."""
        queue = get_queue()

        if job_state == "all":
            jobs = await _list_all_jobs(queue)
        else:
            jobs = []
            try:
                for j in await queue.list_jobs(job_state):
                    jobs.append(_format_job(j, job_state))
            except Exception:
                pass

        total = len(jobs)
        start = (page - 1) * size
        end = start + size
        page_jobs = jobs[start:end]
        total_pages = max(1, (total + size - 1) // size)

        return {
            "jobs": page_jobs,
            "total": total,
            "page": page,
            "size": size,
            "total_pages": total_pages,
            "state": job_state,
        }

    # ------------------------------------------------------------------
    # Repeatables
    # ------------------------------------------------------------------

    @get("/dashboard/repeatables")
    async def get_dashboard_repeatables(self) -> dict:
        """List all repeatable job definitions."""
        queue = get_queue()
        repeatables = await _get_repeatables(queue)
        return {"repeatables": repeatables, "total": len(repeatables)}

    # ------------------------------------------------------------------
    # Workers
    # ------------------------------------------------------------------

    @get("/dashboard/workers")
    async def get_dashboard_workers(self) -> dict:
        """List active workers and heartbeats."""
        queue = get_queue()
        backend = get_backend()
        workers = await _get_workers(backend, queue.name)
        now = time.time()

        # Enrich with staleness info
        for w in workers:
            hb = w.get("heartbeat", 0)
            w["seconds_since_heartbeat"] = round(now - hb, 1) if hb else None
            w["is_stale"] = (now - hb) > 60.0 if hb else True

        return {"workers": workers, "total": len(workers)}

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    @get("/dashboard/metrics")
    async def get_dashboard_metrics(self) -> dict:
        """Throughput, failure, and duration metrics."""
        queue = get_queue()

        jobs = await _list_all_jobs(queue)
        status_counts = await _get_status_counts(jobs)

        # Compute average duration for completed jobs
        durations: list[float] = []
        for j in jobs:
            if (
                j["status"] == "completed"
                and j.get("created_at")
                and j.get("last_attempt")
            ):
                try:
                    durations.append(j["last_attempt"] - j["created_at"])
                except Exception:
                    pass

        avg_duration = round(sum(durations) / len(durations), 2) if durations else None

        return {
            "throughput": status_counts.get("completed", 0),
            "failures": status_counts.get("failed", 0),
            "retries": sum(j.get("retries", 0) for j in jobs),
            "avg_duration": avg_duration,
            "status_counts": status_counts,
        }

    # ------------------------------------------------------------------
    # DLQ (Dead Letter Queue) — failed jobs
    # ------------------------------------------------------------------

    @get("/dashboard/dlq")
    async def get_dashboard_dlq(
        self,
        page: int = Parameter(query="page", default=1),
        size: int = Parameter(query="size", default=50),
    ) -> dict:
        """Dead letter queue: list failed jobs."""
        queue = get_queue()
        failed_jobs: list[dict] = []
        try:
            for j in await queue.list_jobs("failed"):
                failed_jobs.append(_format_job(j, "failed"))
        except Exception:
            pass

        total = len(failed_jobs)
        start = (page - 1) * size
        end = start + size
        page_jobs = failed_jobs[start:end]
        total_pages = max(1, (total + size - 1) // size)

        return {
            "jobs": page_jobs,
            "total": total,
            "page": page,
            "size": size,
            "total_pages": total_pages,
        }

    # ------------------------------------------------------------------
    # Job actions: retry / remove / cancel
    # ------------------------------------------------------------------

    @post("/dashboard/jobs/{job_id:str}/retry")
    async def retry_job(self, job_id: str) -> dict:
        """Retry a failed job."""
        queue = get_queue()
        backend = get_backend()
        try:
            await backend.retry_job(queue.name, job_id)
            return {"ok": True, "action": "retry", "job_id": job_id}
        except Exception as e:
            logger.exception("Failed to retry job %s", job_id)
            return {"ok": False, "error": str(e)}

    @post("/dashboard/jobs/{job_id:str}/remove")
    async def remove_job(self, job_id: str) -> dict:
        """Remove a job from the queue."""
        queue = get_queue()
        backend = get_backend()
        try:
            await backend.remove_job(queue.name, job_id)
            return {"ok": True, "action": "remove", "job_id": job_id}
        except Exception as e:
            logger.exception("Failed to remove job %s", job_id)
            return {"ok": False, "error": str(e)}

    @post("/dashboard/jobs/{job_id:str}/cancel")
    async def cancel_queue_job(self, job_id: str) -> dict:
        """Cancel a job."""
        queue = get_queue()
        try:
            await queue.cancel_job(job_id)
            return {"ok": True, "action": "cancel", "job_id": job_id}
        except Exception as e:
            logger.exception("Failed to cancel job %s", job_id)
            return {"ok": False, "error": str(e)}

    # ------------------------------------------------------------------
    # Queue control: pause / resume / clean
    # ------------------------------------------------------------------

    @post("/dashboard/queue/pause")
    async def pause_queue(self) -> dict:
        """Pause the queue — workers stop picking new jobs."""
        queue = get_queue()
        try:
            await queue.pause()
            return {"ok": True, "action": "pause"}
        except Exception as e:
            logger.exception("Failed to pause queue")
            return {"ok": False, "error": str(e)}

    @post("/dashboard/queue/resume")
    async def resume_queue(self) -> dict:
        """Resume a paused queue."""
        queue = get_queue()
        try:
            await queue.resume()
            return {"ok": True, "action": "resume"}
        except Exception as e:
            logger.exception("Failed to resume queue")
            return {"ok": False, "error": str(e)}

    @post("/dashboard/queue/clean")
    async def clean_queue(
        self,
        job_state: str = Parameter(query="state", default="completed"),
        older_than_hours: int = Parameter(query="older_than_hours", default=24),
    ) -> dict:
        """Purge jobs by state and age."""
        queue = get_queue()
        try:
            threshold = time.time() - (older_than_hours * 3600)
            await queue.clean(job_state, older_than=threshold)
            return {
                "ok": True,
                "action": "clean",
                "state": job_state,
                "older_than_hours": older_than_hours,
            }
        except Exception as e:
            logger.exception("Failed to clean queue")
            return {"ok": False, "error": str(e)}
