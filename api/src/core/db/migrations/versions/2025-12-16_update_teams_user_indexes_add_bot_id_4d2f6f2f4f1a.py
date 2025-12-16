# type: ignore
"""update teams_user indexes to include bot_id

Revision ID: 4d2f6f2f4f1a
Revises: b5d949f2e2ef
Create Date: 2025-12-16 00:00:00.000000+00:00

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
revision = "4d2f6f2f4f1a"
down_revision = "b5d949f2e2ef"
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
    op.drop_index("ix_teams_user_aad_scope", table_name="teams_user")
    op.drop_index("ix_teams_user_teams_scope", table_name="teams_user")
    op.create_index(
        "ix_teams_user_aad_scope",
        "teams_user",
        ["aad_object_id", "scope", "bot_id"],
        unique=True,
        postgresql_where=sa.text("aad_object_id IS NOT NULL"),
    )
    op.create_index(
        "ix_teams_user_teams_scope",
        "teams_user",
        ["teams_user_id", "scope", "bot_id"],
        unique=True,
    )


def schema_downgrades() -> None:
    """schema downgrade migrations go here."""
    op.drop_index("ix_teams_user_teams_scope", table_name="teams_user")
    op.drop_index("ix_teams_user_aad_scope", table_name="teams_user")
    op.create_index(
        "ix_teams_user_aad_scope",
        "teams_user",
        ["aad_object_id", "scope"],
        unique=True,
        postgresql_where=sa.text("aad_object_id IS NOT NULL"),
    )
    op.create_index(
        "ix_teams_user_teams_scope",
        "teams_user",
        ["teams_user_id", "scope"],
        unique=True,
    )


def data_upgrades() -> None:
    """Add any optional data upgrade migrations here!"""


def data_downgrades() -> None:
    """Add any optional data downgrade migrations here!"""
