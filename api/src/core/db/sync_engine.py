"""Shared synchronous SQLAlchemy engine for components that require sync DB access.

Used by APScheduler jobstore, OTel span exporter, and Slack OAuth state store.
All three target the same PostgreSQL instance and share a single connection pool
instead of each creating their own (which previously consumed ~60 connections).

Scheduler-specific hardening (BACKEND_FIXES_ROADMAP.md §B.2-§B.4, derived from
docs/scheduler-hang-analysis.md): pool_pre_ping is OFF by default because
APScheduler 3.x calls jobstore methods synchronously from the asyncio event
loop — a blocking SELECT 1 on a half-open TCP connection stalled the whole
API for 30+ seconds. pool_recycle handles stale connections. Socket-level
connect_timeout + server-side statement_timeout cap any DB-side stall to ~10s.
"""

from functools import lru_cache

from sqlalchemy import Engine, create_engine

from core.config.base import (
    get_scheduler_settings,
    get_settings,
    json_serializer_for_sqlalchemy,
)

# PostgreSQL libpq supports key=value connect_args via psycopg2. `options` is
# forwarded to the server and sets statement_timeout for this connection only.
_PG_CONNECT_ARGS: dict[str, object] = {
    "application_name": "magnetui_scheduler",
    "connect_timeout": 5,
    "options": "-c statement_timeout=10000",
}


@lru_cache(maxsize=1)
def get_shared_sync_engine() -> Engine:
    """Return the singleton synchronous engine (lazy-created, cached)."""
    settings = get_settings()
    scheduler_settings = get_scheduler_settings()

    connect_args: dict[str, object] = {}
    sync_url = settings.db.sync_url
    # Only send libpq-specific kwargs to psycopg2; sqlite/other drivers reject them.
    if "postgresql" in sync_url:
        connect_args = dict(_PG_CONNECT_ARGS)

    return create_engine(
        sync_url,
        pool_size=scheduler_settings.SCHEDULER_POOL_SIZE,
        max_overflow=scheduler_settings.SCHEDULER_MAX_POOL_OVERFLOW,
        pool_timeout=scheduler_settings.SCHEDULER_POOL_TIMEOUT,
        pool_recycle=scheduler_settings.SCHEDULER_POOL_RECYCLE,
        pool_pre_ping=scheduler_settings.SCHEDULER_POOL_PRE_PING,
        connect_args=connect_args,
        json_serializer=json_serializer_for_sqlalchemy,
        echo=False,
    )
