"""AsyncMQ-based scheduler manager.

Provides multi-queue setup, startup/shutdown lifecycle hooks, and
helpers to retrieve AsyncMQ queue / backend singletons at runtime.

Architecture
~~~~~~~~~~~~
*  A centralised ``SchedulerManager`` owns one ``Queue`` per workload
   type (sync, evaluation, maintenance, default) – each with its own
   concurrency and rate-limit profile.
*  The built-in AsyncMQ ``repeatable_scheduler`` is used for cron jobs
   (via ``queue.add_repeatable``).
*  ``ASYNCMQ_SETTINGS_MODULE`` points to ``scheduler.settings`` so that
   backend, table names, stalled-job detection, and JSON serialisation
   are configured in one place.
"""

from __future__ import annotations

import asyncio
import os
from logging import getLogger
from typing import Any

import asyncpg
from asyncmq.backends.postgres import PostgresBackend
from asyncmq.core.event import event_emitter
from asyncmq.queues import Queue

from core.config.base import get_database_settings, get_scheduler_settings
from scheduler.settings import (
    QUEUE_DEFAULT,
    QUEUE_EVALUATION,
    QUEUE_MAINTENANCE,
    QUEUE_SYNC,
)

logger = getLogger(__name__)

# ---------------------------------------------------------------------------
# DDL – non-destructive (CREATE TABLE IF NOT EXISTS)
# ---------------------------------------------------------------------------

_DDL = """
CREATE TABLE IF NOT EXISTS asyncmq_jobs (
    id SERIAL PRIMARY KEY,
    queue_name TEXT NOT NULL,
    job_id TEXT NOT NULL UNIQUE,
    data JSONB NOT NULL,
    status TEXT,
    delay_until DOUBLE PRECISION,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS asyncmq_repeatables (
    queue_name TEXT NOT NULL,
    job_def    JSONB NOT NULL,
    next_run   TIMESTAMPTZ NOT NULL,
    paused     BOOLEAN     NOT NULL DEFAULT FALSE,
    PRIMARY KEY(queue_name, job_def)
);

CREATE TABLE IF NOT EXISTS asyncmq_cancelled_jobs (
    queue_name TEXT NOT NULL,
    job_id     TEXT NOT NULL,
    PRIMARY KEY(queue_name, job_id)
);

CREATE TABLE IF NOT EXISTS asyncmq_workers_heartbeat (
    worker_id   TEXT PRIMARY KEY,
    queues      TEXT[],
    concurrency INT,
    heartbeat   DOUBLE PRECISION
);

CREATE INDEX IF NOT EXISTS idx_asyncmq_jobs_queue_name  ON asyncmq_jobs(queue_name);
CREATE INDEX IF NOT EXISTS idx_asyncmq_jobs_status      ON asyncmq_jobs(status);
CREATE INDEX IF NOT EXISTS idx_asyncmq_jobs_delay_until ON asyncmq_jobs(delay_until);
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_postgres_dsn() -> str:
    """Build a ``postgresql://`` DSN suitable for asyncpg from settings."""
    db_settings = get_database_settings()
    url = db_settings.effective_url

    for prefix in (
        "postgresql+asyncpg://",
        "postgresql+psycopg2://",
        "postgresql+psycopg://",
    ):
        if url.startswith(prefix):
            return url.replace(prefix, "postgresql://")

    if url.startswith("postgresql://"):
        return url

    raise RuntimeError(
        f"Cannot derive a PostgreSQL DSN for AsyncMQ from DATABASE_URL={url!r}. "
        "Ensure DATABASE_URL points to a PostgreSQL database."
    )


async def _ensure_tables(dsn: str) -> None:
    """Create AsyncMQ tables if they do not already exist (non-destructive)."""
    conn = await asyncpg.connect(dsn)
    try:
        await conn.execute(_DDL)
        logger.info("AsyncMQ database tables ensured")
    finally:
        await conn.close()


def _build_cron_expr(cron_config) -> str:
    """Build a standard 5-field cron expression.

    Accepts either:
    * A ``CronConfig`` pydantic model (with individual fields).
    * A plain dict with the same keys.
    * A string already containing a cron expression (returned as-is).
    """
    if isinstance(cron_config, str):
        return cron_config

    if hasattr(cron_config, "cron_expression") and cron_config.cron_expression:
        return cron_config.cron_expression

    data = (
        cron_config.model_dump()
        if hasattr(cron_config, "model_dump")
        else dict(cron_config)
    )
    minute = str(data.get("minute") if data.get("minute") is not None else "*")
    hour = str(data.get("hour") if data.get("hour") is not None else "*")
    day = str(data.get("day") if data.get("day") is not None else "*")
    month = str(data.get("month") if data.get("month") is not None else "*")
    day_of_week = str(
        data.get("day_of_week") if data.get("day_of_week") is not None else "*"
    )
    return f"{minute} {hour} {day} {month} {day_of_week}"


# ---------------------------------------------------------------------------
# Queue ↔ task-type mapping
# ---------------------------------------------------------------------------

# Populated during task registration in executors.py
_TASK_QUEUE_MAP: dict[str, str] = {}
"""Maps ``RunConfigurationType`` value → queue name."""


def get_queue_for_task_type(run_config_type: str) -> str:
    """Return the queue name for a given ``RunConfigurationType``."""
    return _TASK_QUEUE_MAP.get(run_config_type, QUEUE_DEFAULT)


# ---------------------------------------------------------------------------
# SchedulerManager – multi-queue lifecycle
# ---------------------------------------------------------------------------


class SchedulerManager:
    """Manages multiple AsyncMQ queues, their workers, and the backend."""

    def __init__(self) -> None:
        self._backend: PostgresBackend | None = None
        self._queues: dict[str, Queue] = {}
        self._worker_tasks: dict[str, asyncio.Task] = {}

    # -- public accessors ---------------------------------------------------

    @property
    def backend(self) -> PostgresBackend:
        if self._backend is None:
            raise RuntimeError("AsyncMQ backend not initialised. Call startup() first.")
        return self._backend

    def get_queue(self, name: str | None = None) -> Queue:
        """Retrieve a queue by name.  Defaults to ``QUEUE_DEFAULT``."""
        name = name or QUEUE_DEFAULT
        q = self._queues.get(name)
        if q is None:
            raise RuntimeError(
                f"AsyncMQ queue '{name}' not initialised. "
                f"Available: {list(self._queues)}. Call startup() first."
            )
        return q

    @property
    def all_queues(self) -> dict[str, Queue]:
        return dict(self._queues)

    # -- lifecycle ----------------------------------------------------------

    async def startup(self) -> None:
        """Initialise backend, create queues, load recurring jobs, start workers."""

        # Ensure env var is set so AsyncMQ picks up our Settings
        os.environ.setdefault("ASYNCMQ_SETTINGS_MODULE", "scheduler.settings.Settings")

        dsn = _get_postgres_dsn()
        await _ensure_tables(dsn)

        settings = get_scheduler_settings()

        self._backend = PostgresBackend(dsn=dsn)
        await self._backend.connect()

        # Create queues with per-workload concurrency & rate limits
        queue_configs: list[dict[str, Any]] = [
            {
                "name": QUEUE_DEFAULT,
                "concurrency": settings.SCHEDULER_DEFAULT_CONCURRENCY,
            },
            {
                "name": QUEUE_SYNC,
                "concurrency": settings.SCHEDULER_SYNC_CONCURRENCY,
                "rate_limit": settings.SCHEDULER_SYNC_RATE_LIMIT or None,
            },
            {
                "name": QUEUE_EVALUATION,
                "concurrency": settings.SCHEDULER_EVAL_CONCURRENCY,
            },
            {
                "name": QUEUE_MAINTENANCE,
                "concurrency": settings.SCHEDULER_MAINTENANCE_CONCURRENCY,
                "rate_limit": settings.SCHEDULER_MAINTENANCE_RATE_LIMIT or None,
            },
        ]

        for cfg in queue_configs:
            q = Queue(
                name=cfg["name"],
                backend=self._backend,
                concurrency=cfg.get("concurrency", 3),
                rate_limit=cfg.get("rate_limit"),
            )
            self._queues[cfg["name"]] = q

        # Import executors so @task decorators register in TASK_REGISTRY
        import scheduler.executors  # noqa: F401

        # Reload recurring jobs from the application database
        await self._load_recurring_jobs()

        # Register event hooks for observability
        self._register_event_hooks()

        # Start a worker for each queue
        for name, q in self._queues.items():
            task = asyncio.create_task(q.run(), name=f"asyncmq-worker-{name}")
            self._worker_tasks[name] = task
            logger.info(
                "AsyncMQ worker started for queue '%s' (concurrency=%s)",
                name,
                q.concurrency,
            )

    async def shutdown(self) -> None:
        """Cancel all workers and disconnect the backend."""

        for name, task in self._worker_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                logger.info("AsyncMQ worker stopped for queue '%s'", name)
        self._worker_tasks.clear()

        if self._backend:
            await self._backend.close()
            logger.info("AsyncMQ backend disconnected")

        self._queues.clear()
        self._backend = None

    # -- repeatable management ----------------------------------------------

    async def add_repeatable(
        self,
        task_id: str,
        cron: str,
        kwargs: dict[str, Any],
        *,
        queue_name: str | None = None,
        every: float | None = None,
    ) -> None:
        """Register a repeatable job on the appropriate queue.

        After the entry is added the queue's worker is restarted so the
        built-in ``repeatable_scheduler`` re-initialises its cron
        trackers with the updated list.
        """
        qname = queue_name or QUEUE_DEFAULT
        q = self.get_queue(qname)

        entry: dict[str, Any] = {"task_id": task_id, "kwargs": kwargs}
        if cron:
            entry["cron"] = cron
        if every is not None:
            entry["every"] = every

        q.add_repeatable(**entry)
        logger.info(
            "Added repeatable: task_id=%s, cron=%s, queue=%s, job_id=%s",
            task_id,
            cron,
            qname,
            kwargs.get("job_id"),
        )

        # Restart the worker so the repeatable scheduler picks up the
        # new entry (it only reads _repeatables at startup).
        await self._restart_queue_worker(qname)

    async def remove_repeatable_by_job_id(self, job_id: str) -> bool:
        """Remove a repeatable entry across all queues by ``job_id``."""
        removed = False
        affected_queues: list[str] = []
        for name, q in self._queues.items():
            before = len(q._repeatables)
            q._repeatables = [
                r for r in q._repeatables if r.get("kwargs", {}).get("job_id") != job_id
            ]
            if len(q._repeatables) < before:
                removed = True
                affected_queues.append(name)
        if removed:
            logger.info("Removed repeatable for job_id=%s", job_id)
            for qname in affected_queues:
                await self._restart_queue_worker(qname)
        return removed

    async def _restart_queue_worker(self, queue_name: str) -> None:
        """Restart the worker task for *queue_name*.

        This is a no-op when called before workers have been started
        (e.g. during ``_load_recurring_jobs`` at startup).
        """
        task = self._worker_tasks.get(queue_name)
        if task is None or task.done():
            return

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        q = self._queues[queue_name]
        new_task = asyncio.create_task(q.run(), name=f"asyncmq-worker-{queue_name}")
        self._worker_tasks[queue_name] = new_task
        logger.info(
            "Restarted worker for queue '%s' to apply repeatable changes",
            queue_name,
        )

    # -- recurring job loader -----------------------------------------------

    async def _load_recurring_jobs(self) -> None:
        """Read recurring jobs from the application DB and register them
        as repeatables so the built-in scheduler re-enqueues them."""
        try:
            from sqlalchemy import text

            from core.config.app import alchemy
            from scheduler.executors import RUN_CONFIG_HANDLERS
            from scheduler.types import JobDefinition, JobType

            async with alchemy.get_session() as session:
                result = await session.execute(
                    text("""
                        SELECT id, definition FROM jobs
                        WHERE status IN ('Waiting', 'Processing')
                        AND definition->>'job_type' = 'recurring'
                    """)
                )
                rows = result.fetchall()

            count = 0
            for row in rows:
                job_id = str(row[0])
                try:
                    jd = JobDefinition.model_validate(row[1])
                    if jd.job_type != JobType.RECURRING or not jd.cron:
                        continue

                    handler = RUN_CONFIG_HANDLERS.get(jd.run_configuration.type)
                    if handler is None:
                        logger.warning(
                            "No handler for %s, skipping recurring job %s",
                            jd.run_configuration.type,
                            job_id,
                        )
                        continue

                    cron_expr = _build_cron_expr(jd.cron)
                    task_id = handler.task_id

                    # Determine which queue this task belongs to
                    queue_name = get_queue_for_task_type(
                        jd.run_configuration.type.value
                    )

                    await self.add_repeatable(
                        task_id,
                        cron=cron_expr,
                        kwargs={
                            "job_id": job_id,
                            "job_definition": jd.model_dump(mode="json"),
                            "params": jd.run_configuration.params,
                        },
                        queue_name=queue_name,
                    )
                    count += 1
                    logger.info(
                        "Restored recurring job %s with cron '%s' → queue '%s'",
                        job_id,
                        cron_expr,
                        queue_name,
                    )
                except Exception as e:
                    logger.error("Failed to restore recurring job %s: %s", job_id, e)

            logger.info("Loaded %d recurring job(s) from database", count)
        except Exception as e:
            logger.error("Failed to load recurring jobs: %s", e)

    # -- event hooks --------------------------------------------------------

    def _register_event_hooks(self) -> None:
        """Subscribe to AsyncMQ lifecycle events for observability."""

        def _on_started(payload: dict) -> None:
            logger.debug(
                "job:started – id=%s task=%s",
                payload.get("id"),
                payload.get("task_id"),
            )

        def _on_completed(payload: dict) -> None:
            ts = payload.get("timestamps", {})
            duration = None
            if ts.get("finished_at") and ts.get("created_at"):
                try:
                    duration = round(ts["finished_at"] - ts["created_at"], 3)
                except Exception:
                    pass
            logger.info(
                "job:completed – id=%s task=%s duration=%ss",
                payload.get("id"),
                payload.get("task_id"),
                duration,
            )

        def _on_failed(payload: dict) -> None:
            logger.warning(
                "job:failed – id=%s task=%s error=%s",
                payload.get("id"),
                payload.get("task_id"),
                payload.get("error"),
            )

        def _on_progress(payload: dict) -> None:
            logger.debug(
                "job:progress – id=%s progress=%s",
                payload.get("id"),
                payload.get("progress"),
            )

        event_emitter.on("job:started", _on_started)
        event_emitter.on("job:completed", _on_completed)
        event_emitter.on("job:failed", _on_failed)
        event_emitter.on("job:progress", _on_progress)

        logger.info("AsyncMQ event hooks registered for observability")


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_manager: SchedulerManager | None = None


def _get_manager() -> SchedulerManager:
    if _manager is None:
        raise RuntimeError("SchedulerManager not initialised. Call startup() first.")
    return _manager


# ---------------------------------------------------------------------------
# Public API (backward-compatible function signatures)
# ---------------------------------------------------------------------------


async def startup() -> None:
    """Initialise the scheduler manager (called from Litestar on_startup)."""
    global _manager
    _manager = SchedulerManager()
    await _manager.startup()


async def shutdown() -> None:
    """Shutdown the scheduler manager (called from Litestar on_shutdown)."""
    global _manager
    if _manager:
        await _manager.shutdown()
    _manager = None


def get_queue(name: str | None = None) -> Queue:
    """Retrieve a queue by name.  Defaults to ``QUEUE_DEFAULT``."""
    return _get_manager().get_queue(name)


def get_backend() -> PostgresBackend:
    """Retrieve the AsyncMQ backend singleton."""
    return _get_manager().backend


async def add_repeatable(
    task_id: str,
    cron: str,
    kwargs: dict[str, Any],
    *,
    queue_name: str | None = None,
    every: float | None = None,
) -> None:
    """Register a repeatable job.  Delegates to the manager."""
    await _get_manager().add_repeatable(
        task_id, cron=cron, kwargs=kwargs, queue_name=queue_name, every=every
    )


async def remove_repeatable_by_job_id(job_id: str) -> bool:
    """Remove a repeatable entry by its ``job_id``."""
    return await _get_manager().remove_repeatable_by_job_id(job_id)
