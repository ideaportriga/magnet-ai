# type: ignore
"""Add `note_taker_integration_attempt` — journal of side-effect publishes.

Stage 2 of the note-taker pipeline pushes a finished recording into
Confluence, Salesforce, and Knowledge Graph. Without a journal we can't
tell whether a missing summary in Confluence means "we never tried" or
"we tried and the API was down" — and we duplicate work on re-runs.

This table records one row per ``(job_id, integration_kind)`` with a
unique constraint that makes re-runs idempotent at the database level.

See docs/NOTE_TAKER_RELIABILITY_PLAN.md § P1-4 (phase 1).

Revision ID: a4b5c6d7e8f9
Revises: f3a4b5c6d7e8
Create Date: 2026-05-11 00:02:00.000000+00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

__all__ = ["downgrade", "upgrade"]

revision = "a4b5c6d7e8f9"
down_revision = "f3a4b5c6d7e8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "note_taker_integration_attempt",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("job_id", sa.Text(), nullable=False),
        sa.Column(
            "integration_kind",
            sa.Text(),
            nullable=False,
            comment="confluence | salesforce | knowledge_graph",
        ),
        sa.Column(
            "status",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'pending'"),
            comment="pending | done | failed",
        ),
        sa.Column(
            "attempt_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("error_class", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "job_id",
            "integration_kind",
            name="uq_note_taker_integration_attempt_job_kind",
        ),
    )
    op.create_index(
        "ix_note_taker_integration_attempt_status",
        "note_taker_integration_attempt",
        ["status"],
    )
    op.create_index(
        "ix_note_taker_integration_attempt_job_id",
        "note_taker_integration_attempt",
        ["job_id"],
    )
    op.create_index(
        "ix_note_taker_integration_attempt_trace_id",
        "note_taker_integration_attempt",
        ["trace_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_note_taker_integration_attempt_trace_id",
        table_name="note_taker_integration_attempt",
    )
    op.drop_index(
        "ix_note_taker_integration_attempt_job_id",
        table_name="note_taker_integration_attempt",
    )
    op.drop_index(
        "ix_note_taker_integration_attempt_status",
        table_name="note_taker_integration_attempt",
    )
    op.drop_table("note_taker_integration_attempt")
