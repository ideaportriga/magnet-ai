# type: ignore
"""Add `trace_id` columns to notetaker tables for cross-stage correlation.

A single trace_id is generated when a Graph webhook arrives (or when an
admin preview job is enqueued) and propagated through STT, post-processing,
and integration publishes. Each table that carries pipeline state gets a
nullable, indexed ``trace_id`` column so log searches in Loki can join the
whole flow on one identifier.

See docs/NOTE_TAKER_RELIABILITY_PLAN.md § P1-3.

Revision ID: f3a4b5c6d7e8
Revises: e2f3a4b5c6d7
Create Date: 2026-05-11 00:01:00.000000+00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

__all__ = ["downgrade", "upgrade"]

revision = "f3a4b5c6d7e8"
down_revision = "e2f3a4b5c6d7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("note_taker_jobs", sa.Column("trace_id", sa.Text(), nullable=True))
    op.create_index("ix_note_taker_jobs_trace_id", "note_taker_jobs", ["trace_id"])

    op.add_column(
        "note_taker_pending_confirmation",
        sa.Column("trace_id", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_note_taker_pending_confirmation_trace_id",
        "note_taker_pending_confirmation",
        ["trace_id"],
    )

    op.add_column("transcriptions", sa.Column("trace_id", sa.Text(), nullable=True))
    op.create_index("ix_transcriptions_trace_id", "transcriptions", ["trace_id"])


def downgrade() -> None:
    op.drop_index("ix_transcriptions_trace_id", table_name="transcriptions")
    op.drop_column("transcriptions", "trace_id")

    op.drop_index(
        "ix_note_taker_pending_confirmation_trace_id",
        table_name="note_taker_pending_confirmation",
    )
    op.drop_column("note_taker_pending_confirmation", "trace_id")

    op.drop_index("ix_note_taker_jobs_trace_id", table_name="note_taker_jobs")
    op.drop_column("note_taker_jobs", "trace_id")
