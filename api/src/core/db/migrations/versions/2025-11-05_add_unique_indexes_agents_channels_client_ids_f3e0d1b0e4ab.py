# type: ignore
"""Add unique indexes for channel client IDs

Revision ID: f3e0d1b0e4ab
Revises: 08ef6eb138ef
Create Date: 2025-11-05 14:20:00.000000+00:00

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
revision = "f3e0d1b0e4ab"
down_revision = "08ef6eb138ef"
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
    op.create_index(
        "uq_agents_ms_teams_client_id",
        "agents",
        [sa.text("(channels #>> '{ms_teams,client_id}')")],
        unique=True,
        postgresql_where=sa.text(
            "COALESCE(channels -> 'ms_teams' ->> 'client_id', '') <> ''"
        ),
    )

    op.create_index(
        "uq_agents_slack_client_id",
        "agents",
        [sa.text("(channels #>> '{slack,client_id}')")],
        unique=True,
        postgresql_where=sa.text(
            "COALESCE(channels -> 'slack' ->> 'client_id', '') <> ''"
        ),
    )


def schema_downgrades() -> None:
    """schema downgrade migrations go here."""
    op.drop_index("uq_agents_slack_client_id", table_name="agents")
    op.drop_index("uq_agents_ms_teams_client_id", table_name="agents")


def data_upgrades() -> None:
    """Add any optional data upgrade migrations here!"""


def data_downgrades() -> None:
    """Add any optional data downgrade migrations here!"""


