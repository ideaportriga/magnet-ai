# type: ignore
"""add teams meeting table

Revision ID: 7b9a2f4d1c3e
Revises: 9d96f91c6c78
Create Date: 2025-12-08 12:00:00.000000+00:00

"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op
from advanced_alchemy.types import DateTimeUTC, GUID
import advanced_alchemy.types
import advanced_alchemy.types.datetime
import advanced_alchemy.types.json
from sqlalchemy.dialects import postgresql

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

sa.GUID = GUID
sa.DateTimeUTC = DateTimeUTC


# revision identifiers, used by Alembic.
revision = "7b9a2f4d1c3e"
down_revision = "9d96f91c6c78"
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
        "teams_meeting",
        sa.Column(
            "chat_id",
            sa.Text(),
            nullable=False,
            comment="Teams meeting chat / conversation ID",
        ),
        sa.Column(
            "graph_online_meeting_id",
            sa.Text(),
            nullable=True,
            comment="Graph OnlineMeeting ID for recording subscriptions",
        ),
        sa.Column(
            "join_url",
            sa.Text(),
            nullable=True,
            comment="Meeting join link",
        ),
        sa.Column(
            "title",
            sa.Text(),
            nullable=True,
            comment="Meeting subject/title",
        ),
        sa.Column(
            "is_bot_installed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
            comment="Whether the bot is currently installed in the meeting",
        ),
        sa.Column(
            "removed_from_meeting_at",
            advanced_alchemy.types.datetime.DateTimeUTC(timezone=True),
            nullable=True,
            comment="Timestamp when the bot was removed from the meeting",
        ),
        sa.Column(
            "subscription_id",
            sa.Text(),
            nullable=True,
            comment="Graph subscription ID for recordings",
        ),
        sa.Column(
            "subscription_expires_at",
            advanced_alchemy.types.datetime.DateTimeUTC(timezone=True),
            nullable=True,
            comment="Cached subscription expiration time",
        ),
        sa.Column(
            "subscription_is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            comment="Whether the subscription is currently active",
        ),
        sa.Column(
            "subscription_last_error",
            sa.Text(),
            nullable=True,
            comment="Last error received while managing the subscription",
        ),
        sa.Column(
            "subscription_conversation_reference",
            sa.JSON().with_variant(
                postgresql.JSONB(astext_type=sa.Text()), "postgresql"
            ),
            nullable=True,
            comment="ConversationReference snapshot for proactive messaging",
        ),
        sa.Column(
            "last_seen_at",
            advanced_alchemy.types.datetime.DateTimeUTC(timezone=True),
            nullable=True,
            comment="Last time the bot observed activity in this meeting",
        ),
        sa.Column(
            "last_recordings_check_at",
            advanced_alchemy.types.datetime.DateTimeUTC(timezone=True),
            nullable=True,
            comment="Last time recordings were checked for this meeting",
        ),
        sa.Column(
            "extra",
            sa.JSON().with_variant(
                postgresql.JSONB(astext_type=sa.Text()), "postgresql"
            ),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
            comment="Additional metadata",
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
        sa.Column(
            "id",
            sa.BigInteger(),
            sa.Sequence("teams_meeting_id_seq", optional=False),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_teams_meeting")),
        sa.UniqueConstraint("chat_id", name=op.f("uq_teams_meeting_chat_id")),
        sa.UniqueConstraint(
            "graph_online_meeting_id",
            name=op.f("uq_teams_meeting_graph_online_meeting_id"),
        ),
        sa.UniqueConstraint(
            "subscription_id", name=op.f("uq_teams_meeting_subscription_id")
        ),
    )
    op.create_index(
        op.f("ix_teams_meeting_graph_online_meeting_id"),
        "teams_meeting",
        ["graph_online_meeting_id"],
        unique=False,
    )


def schema_downgrades() -> None:
    """schema downgrade migrations go here."""
    op.drop_index(
        op.f("ix_teams_meeting_graph_online_meeting_id"),
        table_name="teams_meeting",
    )
    op.drop_table("teams_meeting")


def data_upgrades() -> None:
    """Add any optional data upgrade migrations here!"""


def data_downgrades() -> None:
    """Add any optional data downgrade migrations here!"""
