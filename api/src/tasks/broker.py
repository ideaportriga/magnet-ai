"""TaskIQ broker + result backend + middlewares.

AsyncpgBroker uses PostgreSQL LISTEN/NOTIFY for message delivery and an atomic
`UPDATE … WHERE status='pending' RETURNING` claim for multi-worker safety.

This module is imported by:
- The Litestar API process (to enqueue tasks via `task.kiq(...)`).
- The TaskIQ worker process (to execute tasks).
- The TaskIQ scheduler process (to read schedule sources).

`taskiq-litestar` wires `broker.startup()/shutdown()` into the Litestar app
lifecycle. Worker/scheduler processes run their own startup via the CLI.
"""

from __future__ import annotations

from logging import getLogger

# CLI-launched `taskiq worker` / `taskiq scheduler` processes don't go through
# `app.py`, so they never call `load_env()`. Without this, DSN falls back to
# the shipped default (`test_magnet_ai`) and the broker fails to connect.
# The API process also imports this module after env is loaded, so calling
# load_env() here is idempotent.
from config.config import load_env as _load_env

_load_env()

# Wire Loki / structlog before broker / middleware imports — the latter
# call `getLogger(__name__)` at import time, and we want their first emit
# to land on a configured root. Idempotent: a no-op if Litestar's
# StructlogPlugin already attached the handler.
from tasks.logging_setup import setup_taskiq_logging as _setup_taskiq_logging  # noqa: E402

_setup_taskiq_logging()

from taskiq_pg.asyncpg import AsyncpgBroker, AsyncpgResultBackend  # noqa: E402

from core.config.base import get_settings  # noqa: E402
from tasks.middlewares.enqueue_logging import EnqueueLoggingMiddleware  # noqa: E402
from tasks.middlewares.lifecycle import PerTaskLifecycleMiddleware  # noqa: E402
from tasks.middlewares.retry import PerTaskTypeRetryMiddleware  # noqa: E402
from tasks.middlewares.tracing import TraceContextMiddleware  # noqa: E402

logger = getLogger(__name__)


def _postgres_dsn() -> str:
    """Plain postgres:// DSN for asyncpg (strip SQLAlchemy driver suffix)."""
    settings = get_settings()
    url = settings.db.effective_url
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql://", 1)
    if url.startswith("postgres+asyncpg://"):
        return url.replace("postgres+asyncpg://", "postgres://", 1)
    return url


# asyncpg's create_pool defaults to min_size=10, max_size=10. With 3 pools
# per runtime (broker write, result backend, schedule source) the in-process
# single-container layout keeps this comfortably below PG's default
# max_connections=100. Cap each pool at 2 anyway.
#
# Known limitation for Azure deploy: asyncpg does NOT expose TCP keepalive
# parameters (no equivalent of libpq's `keepalives_idle`). The broker's
# dedicated LISTEN connection (`_read_conn`) is the only at-risk path —
# Azure load balancer NATs aggressively close idle TCP flows. If this turns
# out to bite in Phase 3 smoke-testing, options:
#   1. set kernel-level keepalive defaults via securityContext sysctls,
#   2. add a periodic application-level NOTIFY heartbeat,
#   3. wrap `_read_conn` with a watchdog that reconnects on long quiet
#      windows.
# For now we trust the default behaviour and verify on staging.
_POOL_KWARGS: dict[str, int] = {"min_size": 1, "max_size": 2}


broker = (
    AsyncpgBroker(
        _postgres_dsn(),
        # The broker also keeps a dedicated read-connection for LISTEN/NOTIFY,
        # plus a small write pool for INSERT/UPDATE of taskiq_messages.
        write_kwargs=_POOL_KWARGS,
    )
    .with_result_backend(
        AsyncpgResultBackend(_postgres_dsn(), **_POOL_KWARGS),
    )
    .with_middlewares(
        # Order matters: tracing first (wraps all subsequent logs in a span),
        # enqueue logging after trace so the log line is inside the parent
        # span, lifecycle third (owns the per-task session + cleanup), retry
        # last (decides redelivery based on final error state).
        TraceContextMiddleware(),
        EnqueueLoggingMiddleware(),
        PerTaskLifecycleMiddleware(),
        PerTaskTypeRetryMiddleware(),
    )
)


# Worker-only startup/shutdown hooks. We do NOT use `taskiq_litestar.init`
# here — it enters `app.lifespan()` on WORKER_STARTUP and tries to exit it on
# WORKER_SHUTDOWN, but those two events run on different asyncio tasks.
# Litestar's lifespan wraps an `anyio.create_task_group()` whose cancel scope
# must be exited in the same task — breaking this rule raises a RuntimeError
# that `taskiq_litestar` swallows as a warning, leaving the task group
# un-closed and the worker process hanging on shutdown (required SIGKILL).
#
# Our replacement (`tasks.worker_lifecycle`) initialises only the bits the
# tasks actually need (DB / pgvector / storage), without dragging the
# full Litestar lifespan machinery into the worker.
from tasks.worker_lifecycle import init as _init_worker_lifecycle  # noqa: E402

_init_worker_lifecycle(broker)
