# type: ignore
"""add slack oauth state table

Revision ID: f9d9c0b1d4b2
Revises: c7a1a61f2345
Create Date: 2025-10-26 10:00:00.000000+00:00

"""
from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op
from advanced_alchemy.types import DateTimeUTC, GUID
import advanced_alchemy.types
import advanced_alchemy.types.datetime

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = [
    "downgrade",
    "upgrade",
    "schema_upgrades",
    "schema_downgrades",
    "data_upgrades",
    "data_downgrades",
]

sa.GUID = GUID
sa.DateTimeUTC = DateTimeUTC


# revision identifiers, used by Alembic.
revision = "f9d9c0b1d4b2"
down_revision = "c7a1a61f2345"
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
    op.create_table(
        "slack_oauth_states",
        sa.Column(
            "state_token",
            sa.String(length=255),
            nullable=False,
            comment="Slack OAuth state token",
        ),
        sa.Column(
            "agent_system_name",
            sa.String(length=255),
            nullable=False,
            comment="Associated agent system name",
        ),
        sa.Column(
            "agent_display_name",
            sa.String(length=255),
            nullable=True,
            comment="Human readable agent name",
        ),
        sa.Column(
            "expires_at",
            advanced_alchemy.types.datetime.DateTimeUTC(timezone=True),
            nullable=False,
            comment="Expiration timestamp for the state token",
        ),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            advanced_alchemy.types.datetime.DateTimeUTC(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            advanced_alchemy.types.datetime.DateTimeUTC(timezone=True),
            nullable=False,
        ),
        sa.Column("id", GUID, nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_slack_oauth_states")),
        sa.UniqueConstraint("state_token", name=op.f("uq_slack_oauth_states_state")),
    )
    op.create_index(
        op.f("ix_slack_oauth_states_agent"),
        "slack_oauth_states",
        ["agent_system_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_slack_oauth_states_expires_at"),
        "slack_oauth_states",
        ["expires_at"],
        unique=False,
    )


def schema_downgrades() -> None:
    """schema downgrade migrations go here."""
    op.drop_index(
        op.f("ix_slack_oauth_states_expires_at"),
        table_name="slack_oauth_states",
    )
    op.drop_index(op.f("ix_slack_oauth_states_agent"), table_name="slack_oauth_states")
    op.drop_table("slack_oauth_states")


def data_upgrades() -> None:
    """Add any optional data upgrade migrations here!"""


def data_downgrades() -> None:
    """Add any optional data downgrade migrations here!"""
