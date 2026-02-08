"""AsyncMQ settings module.

Centralizes all AsyncMQ configuration into a single ``Settings`` subclass.
Point AsyncMQ at this module via the environment variable::

    export ASYNCMQ_SETTINGS_MODULE=scheduler.settings.AsyncMQSettings

This replaces manual ``PostgresBackend`` construction, DDL management,
and scattered configuration.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from decimal import Decimal
from functools import partial
from logging import getLogger

from asyncmq.conf.global_settings import Settings as BaseSettings

logger = getLogger(__name__)


# ---------------------------------------------------------------------------
# Queue name constants – each workload type gets its own queue with
# independent concurrency, rate-limiting, and monitoring.
# ---------------------------------------------------------------------------

QUEUE_SYNC = "sync"
"""Heavy data-sync operations (knowledge sources, knowledge graphs)."""

QUEUE_EVALUATION = "evaluation"
"""RAG / prompt evaluation workloads."""

QUEUE_MAINTENANCE = "maintenance"
"""Lightweight recurring maintenance (log cleanup, post-processing)."""

QUEUE_DEFAULT = "default"
"""General purpose / immediate tasks."""

ALL_QUEUES = (QUEUE_DEFAULT, QUEUE_SYNC, QUEUE_EVALUATION, QUEUE_MAINTENANCE)
"""All queue names managed by the scheduler."""


# ---------------------------------------------------------------------------
# Custom JSON serialization to handle UUID, datetime, etc.
# ---------------------------------------------------------------------------


def _json_encoder(obj: object) -> str:
    """Custom JSON encoder for AsyncMQ payloads."""
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


# ---------------------------------------------------------------------------
# AsyncMQ Settings
# ---------------------------------------------------------------------------


def _build_settings() -> type[BaseSettings]:
    """Build the Settings class lazily so we only import heavy deps when
    the settings module is actually loaded by AsyncMQ (via
    ``ASYNCMQ_SETTINGS_MODULE``)."""

    import os

    from core.config.base import get_database_settings, get_scheduler_settings

    db_settings = get_database_settings()
    scheduler_cfg = get_scheduler_settings()

    # Build asyncpg-compatible DSN from the application's DATABASE_URL
    url = db_settings.effective_url
    for prefix in (
        "postgresql+asyncpg://",
        "postgresql+psycopg2://",
        "postgresql+psycopg://",
    ):
        if url.startswith(prefix):
            url = url.replace(prefix, "postgresql://")
            break

    if not url.startswith("postgresql://"):
        raise RuntimeError(
            f"Cannot derive a PostgreSQL DSN for AsyncMQ from DATABASE_URL={url!r}. "
            "Ensure DATABASE_URL points to a PostgreSQL database."
        )

    # Import backend here to avoid top-level heavy import
    from asyncmq.backends.postgres import PostgresBackend

    class AsyncMQSettings(BaseSettings):
        # Backend
        backend: PostgresBackend = PostgresBackend(dsn=url)  # type: ignore[assignment]

        # Worker defaults
        worker_concurrency: int = scheduler_cfg.SCHEDULER_CONCURRENCY

        # Scan / poll interval for delayed & repeatable jobs
        scan_interval: float = float(os.environ.get("SCHEDULER_SCAN_INTERVAL", "1.0"))

        # Stalled job detection
        enable_stalled_check: bool = True
        stalled_check_interval: float = 60.0
        stalled_threshold: float = float(scheduler_cfg.SCHEDULER_JOB_TIMEOUT)

        # Task auto-discovery – modules containing @task decorators
        tasks: list[str] = ["scheduler.executors"]

        # Postgres table names (match existing DDL)
        postgres_jobs_table_name: str = "asyncmq_jobs"
        postgres_repeatables_table_name: str = "asyncmq_repeatables"
        postgres_cancelled_jobs_table_name: str = "asyncmq_cancelled_jobs"

        # Logging
        logging_level: str = os.environ.get("ASYNCMQ_LOG_LEVEL", "INFO")

        # Custom JSON serialization for UUID / datetime
        json_dumps = partial(json.dumps, default=_json_encoder)
        json_loads = json.loads

    return AsyncMQSettings


# Module-level Settings class – instantiated when AsyncMQ reads this module.
Settings = _build_settings()
