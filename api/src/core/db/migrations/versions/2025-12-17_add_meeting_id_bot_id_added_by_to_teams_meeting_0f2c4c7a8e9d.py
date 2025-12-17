# type: ignore
"""add meeting/bot/added_by fields to teams_meeting

Revision ID: 0f2c4c7a8e9d
Revises: 9a82c5c1f8f3
Create Date: 2025-12-17 00:00:00.000000+00:00

"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op

if TYPE_CHECKING:
    pass

__all__ = [
    "downgrade",
    "upgrade",
    "schema_upgrades",
    "schema_downgrades",
    "data_upgrades",
    "data_downgrades",
]


# revision identifiers, used by Alembic.
revision = "0f2c4c7a8e9d"
down_revision = "9a82c5c1f8f3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        with op.get_context().autocommit_block():
            schema_upgrades()
            data_upgrades()


def downgrade() -> None:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        with op.get_context().autocommit_block():
            data_downgrades()
            schema_downgrades()


def schema_upgrades() -> None:
    """schema upgrade migrations go here."""
    op.add_column(
        "teams_meeting",
        sa.Column("meeting_id", sa.Text(), nullable=True),
    )
    op.add_column(
        "teams_meeting",
        sa.Column("bot_id", sa.Text(), nullable=True),
    )
    op.add_column(
        "teams_meeting",
        sa.Column("added_by_user_id", sa.Text(), nullable=True),
    )
    op.add_column(
        "teams_meeting",
        sa.Column("added_by_aad_object_id", sa.Text(), nullable=True),
    )
    op.add_column(
        "teams_meeting",
        sa.Column("added_by_display_name", sa.Text(), nullable=True),
    )


def schema_downgrades() -> None:
    """schema downgrade migrations go here."""
    op.drop_column("teams_meeting", "added_by_display_name")
    op.drop_column("teams_meeting", "added_by_aad_object_id")
    op.drop_column("teams_meeting", "added_by_user_id")
    op.drop_column("teams_meeting", "bot_id")
    op.drop_column("teams_meeting", "meeting_id")


def data_upgrades() -> None:
    """Add any optional data upgrade migrations here!"""


def data_downgrades() -> None:
    """Add any optional data downgrade migrations here!"""
