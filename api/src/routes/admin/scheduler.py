import logging

from litestar import Controller, get, post
from sqlalchemy.ext.asyncio import AsyncSession

from scheduler.job_executor import cancel_job, create_job
from scheduler.types import JobDefinition, JobIdInput

logger = logging.getLogger(__name__)


class SchedulerController(Controller):
    path = "/scheduler"
    tags = ["Admin / Scheduler"]

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

    @get("/queue-status")
    async def get_queue_status(self) -> dict:
        """Get current AsyncMQ queue information including stats, jobs, repeatables and workers."""
        import time

        from scheduler.manager import get_backend, get_queue

        queue = get_queue()
        backend = get_backend()
        now = time.time()

        # Gather stats
        stats = await queue.queue_stats()

        # Queue paused state
        is_paused = False
        try:
            is_paused = await backend.is_queue_paused(queue.name)
        except Exception:
            pass

        # List jobs by state — include all useful fields
        jobs = []
        for state in ("waiting", "active", "completed", "failed", "delayed"):
            try:
                state_jobs = await queue.list_jobs(state)
                for j in state_jobs:
                    jobs.append(
                        {
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
                    )
            except Exception:
                pass

        # List repeatables
        repeatables = []
        try:
            reps = await queue.list_repeatables()
            for rep in reps:
                repeatables.append(
                    {
                        "job_def": rep.job_def,
                        "next_run": rep.next_run,
                        "paused": rep.paused,
                    }
                )
        except Exception:
            pass

        # Workers
        workers = []
        try:
            worker_list = await backend.list_workers(queue.name)
            for w in worker_list:
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

        # Delayed jobs detail
        delayed_jobs = []
        try:
            delayed_list = await backend.list_delayed(queue.name)
            for d in delayed_list:
                delayed_jobs.append(
                    {
                        "job_id": d.job_id,
                        "run_at": d.run_at,
                        "payload": d.payload,
                    }
                )
        except Exception:
            pass

        # Stalled jobs (heartbeat older than 60s)
        stalled_jobs = []
        try:
            stalled = await backend.fetch_stalled_jobs(older_than=60.0)
            for s in stalled:
                stalled_jobs.append(
                    {
                        "queue": s.get("queue"),
                        "job_data": s.get("job_data"),
                    }
                )
        except Exception:
            pass

        # Status counts
        status_counts: dict[str, int] = {}
        for j in jobs:
            st = j.get("status", "unknown")
            status_counts[st] = status_counts.get(st, 0) + 1

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
