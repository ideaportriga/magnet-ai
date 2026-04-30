# type: ignore
"""TaskIQ migration: add jobs.taskiq_schedule_id, drop apscheduler_jobs, add indexes.

Part of the APScheduler → TaskIQ cutover. See docs/TASKIQ_MIGRATION_PLAN.md.

Changes:
- Add `jobs.taskiq_schedule_id` (nullable TEXT) — links user-facing job row to
  the TaskIQ schedule stored in `taskiq_schedules.id`.
- Add partial index on `jobs (status, last_run) WHERE status = 'Processing'` —
  used by the `recover_stuck_processing_jobs` housekeeping task.
- Drop legacy `apscheduler_jobs` table.

TaskIQ's own tables (`taskiq_messages`, `taskiq_results`, `taskiq_schedules`)
are created idempotently by `AsyncpgBroker.startup()` / `AsyncpgResultBackend.startup()`
/ `AsyncpgScheduleSource.startup()`, so we don't manage their DDL here.

Revision ID: a2b3c4d5e6f7
Revises: b9c8d7e6f5a4
Create Date: 2026-04-21 00:00:00.000000+00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

__all__ = ["downgrade", "upgrade"]

revision = "a2b3c4d5e6f7"
down_revision = "b9c8d7e6f5a4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column("taskiq_schedule_id", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_jobs_taskiq_schedule_id",
        "jobs",
        ["taskiq_schedule_id"],
        unique=False,
        postgresql_where=sa.text("taskiq_schedule_id IS NOT NULL"),
    )
    op.create_index(
        "ix_jobs_status_last_run_processing",
        "jobs",
        ["status", "last_run"],
        unique=False,
        postgresql_where=sa.text("status = 'Processing'"),
    )
    op.execute("DROP TABLE IF EXISTS apscheduler_jobs")


def downgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS apscheduler_jobs (
            id VARCHAR(191) NOT NULL PRIMARY KEY,
            next_run_time DOUBLE PRECISION,
            job_state BYTEA NOT NULL
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_apscheduler_jobs_next_run_time "
        "ON apscheduler_jobs (next_run_time)"
    )
    op.drop_index("ix_jobs_status_last_run_processing", table_name="jobs")
    op.drop_index("ix_jobs_taskiq_schedule_id", table_name="jobs")
    op.drop_column("jobs", "taskiq_schedule_id")
