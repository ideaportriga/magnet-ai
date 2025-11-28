# type: ignore
"""add slack installation storage

Revision ID: c7a1a61f2345
Revises: f82c14db4dfc
Create Date: 2025-10-25 12:00:00.000000+00:00

"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op
from advanced_alchemy.types import DateTimeUTC, GUID
import advanced_alchemy.types
import advanced_alchemy.types.datetime

from core.db.types import EncryptedJsonB

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
sa.EncryptedJsonB = EncryptedJsonB


# revision identifiers, used by Alembic.
revision = "c7a1a61f2345"
down_revision = "f82c14db4dfc"
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
        "slack_installations",
        sa.Column(
            "agent_system_name",
            sa.String(length=255),
            nullable=False,
            comment="Associated agent system name",
        ),
        sa.Column(
            "client_id",
            sa.String(length=255),
            nullable=False,
            comment="Slack app client ID",
        ),
        sa.Column(
            "app_id",
            sa.String(length=255),
            nullable=True,
            comment="Slack app ID",
        ),
        sa.Column(
            "enterprise_id",
            sa.String(length=255),
            nullable=True,
            comment="Slack enterprise ID when installed for an org",
        ),
        sa.Column(
            "team_id",
            sa.String(length=255),
            nullable=True,
            comment="Slack workspace/team ID",
        ),
        sa.Column(
            "user_id",
            sa.String(length=255),
            nullable=False,
            comment="Installer Slack user ID",
        ),
        sa.Column(
            "is_enterprise_install",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            comment="Whether the installation covers the entire enterprise",
        ),
        sa.Column(
            "installed_at",
            advanced_alchemy.types.datetime.DateTimeUTC(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment="Timestamp when the installation was completed",
        ),
        sa.Column(
            "installation_data",
            EncryptedJsonB(key="my-secret-key-tsmh5r"),
            nullable=False,
            comment="Full installation payload (encrypted)",
        ),
        sa.Column(
            "bot_data",
            EncryptedJsonB(key="my-secret-key-tsmh5r"),
            nullable=True,
            comment="Bot token payload (encrypted)",
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_slack_installations")),
        sa.UniqueConstraint(
            "client_id",
            "enterprise_id",
            "team_id",
            "user_id",
            name=op.f("uq_slack_installations_scope"),
        ),
    )
    op.create_index(
        op.f("ix_slack_installations_agent"),
        "slack_installations",
        ["agent_system_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_slack_installations_client_scope"),
        "slack_installations",
        ["client_id", "enterprise_id", "team_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_slack_installations_user"),
        "slack_installations",
        ["user_id"],
        unique=False,
    )


def schema_downgrades() -> None:
    """schema downgrade migrations go here."""
    op.drop_index(op.f("ix_slack_installations_user"), table_name="slack_installations")
    op.drop_index(
        op.f("ix_slack_installations_client_scope"),
        table_name="slack_installations",
    )
    op.drop_index(
        op.f("ix_slack_installations_agent"), table_name="slack_installations"
    )
    op.drop_table("slack_installations")


def data_upgrades() -> None:
    """Add any optional data upgrade migrations here!"""


def data_downgrades() -> None:
    """Add any optional data downgrade migrations here!"""
