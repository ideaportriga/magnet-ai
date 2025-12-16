# type: ignore
"""add teams user table

Revision ID: b5d949f2e2ef
Revises: ca19414774ee
Create Date: 2025-12-15 00:00:00.000000+00:00

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
revision = "b5d949f2e2ef"
down_revision = "ca19414774ee"
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
        "teams_user",
        sa.Column(
            "aad_object_id",
            sa.Text(),
            nullable=True,
            comment="AAD object id from activity.from.aad_object_id",
        ),
        sa.Column(
            "teams_user_id",
            sa.Text(),
            nullable=False,
            comment="Teams user id from activity.from.id",
        ),
        sa.Column(
            "user_principal_name",
            sa.Text(),
            nullable=True,
            comment="User principal name from roster lookup",
        ),
        sa.Column(
            "email",
            sa.Text(),
            nullable=True,
            comment="Email from roster lookup (may be null)",
        ),
        sa.Column(
            "display_name",
            sa.Text(),
            nullable=True,
            comment="Display name from the activity",
        ),
        sa.Column(
            "scope",
            sa.Text(),
            nullable=False,
            comment='Teams scope: "personal" | "groupChat" | "channel"',
        ),
        sa.Column(
            "conversation_id",
            sa.Text(),
            nullable=False,
            comment="Conversation id for proactive messages",
        ),
        sa.Column(
            "service_url",
            sa.Text(),
            nullable=False,
            comment="Channel service URL",
        ),
        sa.Column(
            "bot_id",
            sa.Text(),
            nullable=False,
            comment="Bot's Teams id (activity.recipient.id)",
        ),
        sa.Column(
            "conversation_reference",
            sa.JSON().with_variant(
                postgresql.JSONB(astext_type=sa.Text()), "postgresql"
            ),
            nullable=False,
            comment="Serialized conversation reference snapshot",
        ),
        sa.Column(
            "last_seen_at",
            advanced_alchemy.types.datetime.DateTimeUTC(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            comment="Updated on every message/install event",
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_teams_user")),
    )
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


def schema_downgrades() -> None:
    """schema downgrade migrations go here."""
    op.drop_index("ix_teams_user_teams_scope", table_name="teams_user")
    op.drop_index("ix_teams_user_aad_scope", table_name="teams_user")
    op.drop_table("teams_user")


def data_upgrades() -> None:
    """Add any optional data upgrade migrations here!"""


def data_downgrades() -> None:
    """Add any optional data downgrade migrations here!"""
