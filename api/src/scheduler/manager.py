"""AsyncMQ-based scheduler manager.

Provides queue setup, startup/shutdown lifecycle hooks, a custom
repeatable-job scheduler, and helpers to retrieve the AsyncMQ queue /
backend singletons at runtime.

The built-in ``repeatable_scheduler`` shipped with AsyncMQ has two
limitations that make it unsuitable for our use-case:

1. It is only started inside ``run_worker()`` when the ``repeatables``
   list is **non-empty** at startup time.  If no recurring jobs exist in
   the DB when the server starts, the scheduler coroutine is never
   created, and any repeatables added later at runtime are never
   processed.

2. It initialises ``cron_trackers`` / ``next_runs`` dicts **once** during
   startup.  Cron entries appended to the list after that point cause a
   ``KeyError`` because no tracker exists for them.

We therefore maintain our own repeatable list (``_repeatables``) and run
a custom ``_repeatable_scheduler_loop`` as a separate ``asyncio.Task``.
``queue._repeatables`` is deliberately left empty so that
``queue.run()`` never starts the built-in scheduler (avoiding
duplicates).
"""

from __future__ import annotations

import asyncio
import time as _time
from logging import getLogger
from typing import Any

import asyncpg
from asyncmq.backends.postgres import PostgresBackend
from asyncmq.jobs import Job
from asyncmq.queues import Queue
from croniter import croniter

from core.config.base import get_database_settings, get_scheduler_settings

logger = getLogger(__name__)

QUEUE_NAME = "scheduler"

# Module-level singletons
_queue: Queue | None = None
_backend: PostgresBackend | None = None
_worker_task: asyncio.Task | None = None
_scheduler_task: asyncio.Task | None = None
_repeatables: list[dict[str, Any]] = []

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
    """Build a standard 5-field cron expression from a ``CronConfig`` model."""
    cron_params = {k: v for k, v in cron_config.model_dump().items() if v is not None}
    minute = str(cron_params.get("minute", "*"))
    hour = str(cron_params.get("hour", "*"))
    day = str(cron_params.get("day", "*"))
    month = str(cron_params.get("month", "*"))
    day_of_week = str(cron_params.get("day_of_week", "*"))
    return f"{minute} {hour} {day} {month} {day_of_week}"


# ---------------------------------------------------------------------------
# Custom repeatable scheduler
# ---------------------------------------------------------------------------


async def _repeatable_scheduler_loop() -> None:
    """Custom repeatable scheduler that handles dynamically added cron jobs.

    Unlike AsyncMQ's built-in ``repeatable_scheduler``, this coroutine:
    * Runs unconditionally (even when ``_repeatables`` starts empty).
    * Lazily initialises ``cron_trackers`` for entries added at runtime.
    * Uses a **per-job unique key** (``kwargs.job_id``) so that two
      recurring jobs sharing the same task function are tracked
      independently.
    * Cleans up stale trackers when entries are removed.
    """
    cron_trackers: dict[str, croniter] = {}
    next_runs: dict[str, float] = {}
    check_interval = 30.0

    while True:
        try:
            now = _time.time()

            # Iterate over a snapshot so mutations during iteration are safe
            for job_def in list(_repeatables):
                # Unique key per recurring job (our jobs always carry job_id)
                jkwargs = job_def.get("kwargs", {})
                tracker_key = jkwargs.get("job_id") or job_def["task_id"]
                task_id = job_def["task_id"]

                job_data: dict[str, Any] = {
                    "task_id": task_id,
                    "args": job_def.get("args", []),
                    "kwargs": jkwargs,
                    "retries": job_def.get("retries", 0),
                    "max_retries": job_def.get("max_retries", 3),
                    "ttl": job_def.get("ttl"),
                    "priority": job_def.get("priority", 5),
                }

                if "cron" in job_def:
                    # Lazily initialise tracker for NEW entries
                    if tracker_key not in cron_trackers:
                        itr = croniter(job_def["cron"], now)
                        cron_trackers[tracker_key] = itr
                        next_runs[tracker_key] = itr.get_next(float)
                        logger.debug(
                            "Initialised cron tracker for %s, next run at %s",
                            tracker_key,
                            next_runs[tracker_key],
                        )

                    if now >= next_runs[tracker_key]:
                        job = Job(**job_data)  # type: ignore[arg-type]
                        await _backend.enqueue(_queue.name, job.to_dict())  # type: ignore[union-attr]
                        next_runs[tracker_key] = cron_trackers[tracker_key].get_next(
                            float
                        )
                        logger.info(
                            "Enqueued repeatable %s, next at %s",
                            tracker_key,
                            next_runs[tracker_key],
                        )

                elif "every" in job_def:
                    if "_last_run" not in job_def:
                        job_def["_last_run"] = now
                    if now - job_def["_last_run"] >= job_def["every"]:
                        job = Job(**job_data)  # type: ignore[arg-type]
                        await _backend.enqueue(_queue.name, job.to_dict())  # type: ignore[union-attr]
                        job_def["_last_run"] = now

            # Clean up trackers for removed entries
            active_keys = {
                jd.get("kwargs", {}).get("job_id") or jd["task_id"]
                for jd in _repeatables
            }
            for stale in set(cron_trackers) - active_keys:
                del cron_trackers[stale]
                next_runs.pop(stale, None)

            # Dynamic sleep – wake up earliest when next cron fires
            sleep_time = check_interval
            if next_runs:
                earliest = min(next_runs.values())
                sleep_time = max(0.5, min(check_interval, earliest - _time.time()))

        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Error in repeatable scheduler loop")
            sleep_time = 5.0

        await asyncio.sleep(sleep_time)


# ---------------------------------------------------------------------------
# Public helpers for managing repeatables
# ---------------------------------------------------------------------------


def add_repeatable(
    task_id: str,
    cron: str,
    kwargs: dict[str, Any],
    *,
    every: float | None = None,
) -> None:
    """Register a repeatable job.  The custom scheduler will pick it up."""
    entry: dict[str, Any] = {
        "task_id": task_id,
        "args": [],
        "kwargs": kwargs,
        "retries": 0,
        "ttl": None,
        "priority": 5,
    }
    if cron:
        entry["cron"] = cron
    if every is not None:
        entry["every"] = every
    _repeatables.append(entry)
    logger.info(
        "Added repeatable: task_id=%s, cron=%s, job_id=%s",
        task_id,
        cron,
        kwargs.get("job_id"),
    )


def remove_repeatable_by_job_id(job_id: str) -> bool:
    """Remove a repeatable entry by its ``job_id`` (stored in kwargs).

    Returns ``True`` if an entry was removed.
    """
    global _repeatables
    before = len(_repeatables)
    _repeatables = [
        r for r in _repeatables if r.get("kwargs", {}).get("job_id") != job_id
    ]
    removed = len(_repeatables) < before
    if removed:
        logger.info("Removed repeatable for job_id=%s", job_id)
    return removed


async def _load_recurring_jobs(queue: Queue) -> None:
    """Reload recurring jobs from the application's ``jobs`` table and
    register them with our custom scheduler so they are re-enqueued."""
    try:
        from sqlalchemy import text

        from core.config.app import alchemy
        from scheduler.executors import RUN_CONFIG_HANDLERS
        from scheduler.types import JobDefinition, JobType

        async with alchemy.get_session() as session:
            result = await session.execute(
                text("""
                    SELECT id, definition FROM jobs
                    WHERE status IN ('waiting', 'processing')
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
                        f"No handler for {jd.run_configuration.type}, "
                        f"skipping recurring job {job_id}"
                    )
                    continue

                cron_expr = _build_cron_expr(jd.cron)
                task_id = handler.task_id

                add_repeatable(
                    task_id,
                    cron=cron_expr,
                    kwargs={
                        "job_id": job_id,
                        "job_definition": jd.model_dump(mode="json"),
                        "params": jd.run_configuration.params,
                    },
                )
                count += 1
                logger.info(f"Restored recurring job {job_id} with cron '{cron_expr}'")
            except Exception as e:
                logger.error(f"Failed to restore recurring job {job_id}: {e}")

        logger.info(f"Loaded {count} recurring job(s) from database")
    except Exception as e:
        logger.error(f"Failed to load recurring jobs: {e}")


# ---------------------------------------------------------------------------
# Lifecycle hooks
# ---------------------------------------------------------------------------


async def startup() -> None:
    """Initialize AsyncMQ backend, queue, and worker.

    Called from the Litestar ``on_startup`` hook.
    """
    global _queue, _backend, _worker_task, _scheduler_task

    dsn = _get_postgres_dsn()
    await _ensure_tables(dsn)

    settings = get_scheduler_settings()

    _backend = PostgresBackend(dsn=dsn)
    await _backend.connect()

    _queue = Queue(
        name=settings.SCHEDULER_QUEUE_NAME,
        backend=_backend,
        concurrency=settings.SCHEDULER_CONCURRENCY,
    )

    # Import executors so @task decorators register in TASK_REGISTRY
    import scheduler.executors  # noqa: F401

    # Reload recurring jobs from our application database into _repeatables
    await _load_recurring_jobs(_queue)

    # Start our custom repeatable scheduler (always runs, handles dynamic adds)
    _scheduler_task = asyncio.create_task(_repeatable_scheduler_loop())
    logger.info("Custom repeatable scheduler started")

    # Start the worker as a background task.
    # queue._repeatables is empty ⇒ run_worker will NOT start its own
    # repeatable_scheduler, avoiding duplicates with ours.
    _worker_task = asyncio.create_task(_queue.run())
    logger.info(
        f"AsyncMQ worker started for queue '{settings.SCHEDULER_QUEUE_NAME}' "
        f"(concurrency={settings.SCHEDULER_CONCURRENCY})"
    )


async def shutdown() -> None:
    """Shutdown AsyncMQ worker and backend.

    Called from the Litestar ``on_shutdown`` hook.
    """
    global _queue, _backend, _worker_task, _scheduler_task

    if _scheduler_task and not _scheduler_task.done():
        _scheduler_task.cancel()
        try:
            await _scheduler_task
        except asyncio.CancelledError:
            pass
        logger.info("Custom repeatable scheduler stopped")
    _scheduler_task = None

    if _worker_task and not _worker_task.done():
        _worker_task.cancel()
        try:
            await _worker_task
        except asyncio.CancelledError:
            pass
        logger.info("AsyncMQ worker stopped")

    if _backend:
        await _backend.close()
        logger.info("AsyncMQ backend disconnected")

    _queue = None
    _backend = None
    _worker_task = None


# ---------------------------------------------------------------------------
# Public accessors
# ---------------------------------------------------------------------------


def get_queue() -> Queue:
    """Retrieve the scheduler queue singleton."""
    if _queue is None:
        raise RuntimeError("AsyncMQ queue not initialized. Call startup() first.")
    return _queue


def get_backend() -> PostgresBackend:
    """Retrieve the AsyncMQ backend singleton."""
    if _backend is None:
        raise RuntimeError("AsyncMQ backend not initialized. Call startup() first.")
    return _backend
