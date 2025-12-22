# type: ignore
"""add added_to_meeting_at to teams_meeting

Revision ID: 1c3d5e7f9a0b
Revises: 0f2c4c7a8e9d
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
revision = "1c3d5e7f9a0b"
down_revision = "0f2c4c7a8e9d"
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
        sa.Column("added_to_meeting_at", sa.DateTime(timezone=True), nullable=True),
    )


def schema_downgrades() -> None:
    """schema downgrade migrations go here."""
    op.drop_column("teams_meeting", "added_to_meeting_at")


def data_upgrades() -> None:
    """Add any optional data upgrade migrations here!"""


def data_downgrades() -> None:
    """Add any optional data downgrade migrations here!"""
