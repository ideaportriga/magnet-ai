# type: ignore
"""Add `settings_revision` column to note_taker_settings.

Carries a monotonically-increasing schema revision number on each settings
row so future migrations can transform JSONB `config` payloads in-place
(``UPDATE ... WHERE settings_revision < N``). New rows default to the
current revision; existing rows are backfilled to 1.

Revision ID: c20acfe0b890
Revises: a2b3c4d5e6f7
Create Date: 2026-04-29 00:00:00.000000+00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

__all__ = ["downgrade", "upgrade"]

revision = "c20acfe0b890"
down_revision = "a2b3c4d5e6f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "note_taker_settings",
        sa.Column(
            "settings_revision",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
            comment="Schema revision for the `config` JSONB payload.",
        ),
    )


def downgrade() -> None:
    op.drop_column("note_taker_settings", "settings_revision")
