# type: ignore
"""Outbox retry columns on note_taker_integration_attempt.

`retry_payload` (JSONB) — kwargs blob the outbox sweeper passes to the
appropriate background task to replay a failed integration publish.
`next_retry_at` — when the sweeper is allowed to re-enqueue the row; set
on failure via exponential backoff. The sweeper filters
`status='failed' AND attempt_count < N AND next_retry_at <= now()`.

See NOTE_TAKER_REVISION_PLAN.md §3.3 P2-a.

Revision ID: i3j4k5l6m7n8
Revises: h2i3j4k5l6m7
Create Date: 2026-05-18 17:30:00.000000+00:00
"""

from __future__ import annotations

import warnings

from alembic import op

__all__ = ["downgrade", "upgrade", "schema_upgrades", "schema_downgrades"]

revision = "i3j4k5l6m7n8"
down_revision = "h2i3j4k5l6m7"
branch_labels = None
depends_on = None


TABLE = "note_taker_integration_attempt"


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
    op.execute(
        f"""
        ALTER TABLE {TABLE}
            ADD COLUMN IF NOT EXISTS retry_payload JSONB,
            ADD COLUMN IF NOT EXISTS next_retry_at TIMESTAMPTZ
        """
    )
    # Partial index over the rows the sweeper actually queries. Failed +
    # has-payload + has-next-retry is a tiny fraction of the table, so a
    # partial keeps the index small and the scan cheap.
    op.execute(
        f"""
        CREATE INDEX IF NOT EXISTS ix_{TABLE}_retry_ready
            ON {TABLE} (next_retry_at)
            WHERE status = 'failed'
              AND retry_payload IS NOT NULL
              AND next_retry_at IS NOT NULL
        """
    )


def schema_downgrades() -> None:
    op.execute(f"DROP INDEX IF EXISTS ix_{TABLE}_retry_ready")
    op.execute(
        f"""
        ALTER TABLE {TABLE}
            DROP COLUMN IF EXISTS next_retry_at,
            DROP COLUMN IF EXISTS retry_payload
        """
    )
