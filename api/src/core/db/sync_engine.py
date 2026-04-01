"""Shared synchronous SQLAlchemy engine for components that require sync DB access.

Used by APScheduler jobstore, OTel span exporter, and Slack OAuth state store.
All three target the same PostgreSQL instance and share a single connection pool
instead of each creating their own (which previously consumed ~60 connections).
"""

from functools import lru_cache

from sqlalchemy import Engine, create_engine

from core.config.base import get_settings, json_serializer_for_sqlalchemy


@lru_cache(maxsize=1)
def get_shared_sync_engine() -> Engine:
    """Return the singleton synchronous engine (lazy-created, cached)."""
    settings = get_settings()
    return create_engine(
        settings.db.sync_url,
        pool_size=3,
        max_overflow=5,
        pool_pre_ping=True,
        pool_recycle=3600,
        json_serializer=json_serializer_for_sqlalchemy,
        echo=False,
    )
