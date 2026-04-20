# type: ignore
"""Add indexes for foreign keys that lacked one.

See BACKEND_FIXES_ROADMAP.md §C.6.

PostgreSQL does not auto-index FK columns — the parent side has a PK index,
but the child side needs an explicit one for cascade deletes, JOINs, and
ORM `selectinload` to stay cheap. Audit found one missing index in
`knowledge_graph_sources.schedule_job_id`; adding it CONCURRENTLY so prod
writes aren't blocked.

Revision ID: b9c8d7e6f5a4
Revises: a7b8c9d0e1f2
Create Date: 2026-04-17 00:01:00.000000+00:00

"""

from __future__ import annotations

import warnings

from alembic import op

__all__ = [
    "downgrade",
    "upgrade",
    "schema_upgrades",
    "schema_downgrades",
]

revision = "b9c8d7e6f5a4"
down_revision = "a7b8c9d0e1f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        with op.get_context().autocommit_block():
            schema_upgrades()


def downgrade() -> None:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        with op.get_context().autocommit_block():
            schema_downgrades()


def schema_upgrades() -> None:
    # CONCURRENTLY requires autocommit_block (set above) and cannot run
    # inside a transaction. IF NOT EXISTS keeps the migration idempotent
    # for environments that added the index manually.
    op.execute(
        """
        CREATE INDEX CONCURRENTLY IF NOT EXISTS
            ix_knowledge_graph_sources_schedule_job_id
        ON knowledge_graph_sources (schedule_job_id)
        WHERE schedule_job_id IS NOT NULL
        """
    )


def schema_downgrades() -> None:
    op.execute(
        "DROP INDEX CONCURRENTLY IF EXISTS ix_knowledge_graph_sources_schedule_job_id"
    )
