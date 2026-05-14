# type: ignore
"""Add `teams_webhook_event` for at-least-once webhook deduplication.

Microsoft Graph delivers recording-ready / recordings-lifecycle webhooks
at least once. Without a durable receipt table the webhook handler can
trigger duplicate transcription pipelines on every retry.

The unique constraint on (subscription_id, resource_id, change_type) plus
``INSERT ... ON CONFLICT DO NOTHING`` gives the webhook handler an atomic
"first delivery wins" check. The `notification` JSONB column stages the
original payload so a taskiq worker can pick it up even if the API
process restarts between webhook ack and start of processing
(see docs/NOTE_TAKER_RELIABILITY_PLAN.md § P0-1, § P0-2).

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-05-11 00:00:00.000000+00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

__all__ = ["downgrade", "upgrade"]

revision = "e2f3a4b5c6d7"
down_revision = "d1e2f3a4b5c6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "teams_webhook_event",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("subscription_id", sa.Text(), nullable=False),
        sa.Column("resource_id", sa.Text(), nullable=False),
        sa.Column("change_type", sa.Text(), nullable=False),
        sa.Column(
            "webhook_kind",
            sa.Text(),
            nullable=False,
            comment="recordings-ready | recordings-lifecycle",
        ),
        sa.Column("notification", postgresql.JSONB(), nullable=False),
        sa.Column(
            "status",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'received'"),
            comment="received | enqueued | processing | done | failed",
        ),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column(
            "retry_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.UniqueConstraint(
            "subscription_id",
            "resource_id",
            "change_type",
            name="uq_teams_webhook_event_subscription_resource_change",
        ),
    )
    op.create_index(
        "ix_teams_webhook_event_received_at",
        "teams_webhook_event",
        ["received_at"],
    )
    op.create_index(
        "ix_teams_webhook_event_status",
        "teams_webhook_event",
        ["status"],
    )
    op.create_index(
        "ix_teams_webhook_event_trace_id",
        "teams_webhook_event",
        ["trace_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_teams_webhook_event_trace_id", table_name="teams_webhook_event")
    op.drop_index("ix_teams_webhook_event_status", table_name="teams_webhook_event")
    op.drop_index(
        "ix_teams_webhook_event_received_at", table_name="teams_webhook_event"
    )
    op.drop_table("teams_webhook_event")
