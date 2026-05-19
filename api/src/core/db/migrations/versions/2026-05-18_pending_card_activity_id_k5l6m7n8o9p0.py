# type: ignore
"""Add card_activity_id to note_taker_pending_confirmation.

Speaker-mapping cards live in the Teams chat until their TTL expires
(see NOTE_TAKER_REVISION_PLAN.md §3.x / cards UX roadmap Q8). Without
the originating activity id we can't ``update_activity`` them when the
hourly cleanup cron deletes the pending row, so the card stays live and
clicking Confirm produces a confusing "expired or already processed"
text reply. Storing the activity id lets the sweeper proactively swap
the card for a read-only "expired" version.

Revision ID: k5l6m7n8o9p0
Revises: j4k5l6m7n8o9
Create Date: 2026-05-18 21:30:00.000000+00:00
"""

from __future__ import annotations

import warnings

from alembic import op

__all__ = ["downgrade", "upgrade", "schema_upgrades", "schema_downgrades"]

revision = "k5l6m7n8o9p0"
down_revision = "j4k5l6m7n8o9"
branch_labels = None
depends_on = None


TABLE = "note_taker_pending_confirmation"


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
    op.execute(f"ALTER TABLE {TABLE} ADD COLUMN IF NOT EXISTS card_activity_id TEXT")
    # Pipeline progress card activity id — pipeline pauses for speaker
    # confirmation in a worker; the confirm card-action runs in the API
    # process and needs this id to continue updating the same progress
    # card (post-process → confluence → salesforce → kg stages) instead
    # of leaving it stuck at "Generating summary ⏳" forever.
    op.execute(
        f"ALTER TABLE {TABLE} ADD COLUMN IF NOT EXISTS progress_card_activity_id TEXT"
    )


def schema_downgrades() -> None:
    op.execute(f"ALTER TABLE {TABLE} DROP COLUMN IF EXISTS progress_card_activity_id")
    op.execute(f"ALTER TABLE {TABLE} DROP COLUMN IF EXISTS card_activity_id")
