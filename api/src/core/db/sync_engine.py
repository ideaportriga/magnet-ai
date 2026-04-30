"""Shared synchronous SQLAlchemy engine for sync-only callers.

A handful of subsystems need a sync engine:
- OTEL SQLAlchemy exporter (`sqlalchemy_sync_span_exporter.py`) — batch span
  processor runs on a sync thread.
- Slack SDK installation / state stores — the vendor library is sync.
- Alembic migrations — run under a sync engine.

Historically this module also backed the APScheduler jobstore, which is why it
had elaborate pool-sizing config. That's gone — TaskIQ uses asyncpg. Defaults
here are small; bump via `DATABASE_SYNC_POOL_SIZE` if a specific caller needs
more.
"""

from __future__ import annotations

import os
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from core.config.base import get_settings


@lru_cache(maxsize=1)
def get_shared_sync_engine() -> Engine:
    settings = get_settings()
    url = settings.db.sync_url
    return create_engine(
        url,
        pool_size=int(os.environ.get("DATABASE_SYNC_POOL_SIZE", "2")),
        max_overflow=int(os.environ.get("DATABASE_SYNC_POOL_OVERFLOW", "3")),
        pool_timeout=int(os.environ.get("DATABASE_SYNC_POOL_TIMEOUT", "10")),
        pool_recycle=int(os.environ.get("DATABASE_SYNC_POOL_RECYCLE", "3600")),
        pool_pre_ping=True,
        pool_reset_on_return="commit",
    )
