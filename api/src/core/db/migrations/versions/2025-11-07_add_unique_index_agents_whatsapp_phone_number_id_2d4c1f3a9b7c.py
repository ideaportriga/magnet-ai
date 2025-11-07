# type: ignore
"""Add unique index for WhatsApp phone number id in agents channels

Revision ID: 2d4c1f3a9b7c
Revises: f3e0d1b0e4ab
Create Date: 2025-11-07 10:15:00.000000+00:00

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
revision = "2d4c1f3a9b7c"
down_revision = "f3e0d1b0e4ab"
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
        "uq_agents_whatsapp_phone_number_id",
        "agents",
        [sa.text("(channels #>> '{whatsapp,phone_number_id}')")],
        unique=True,
        postgresql_where=sa.text(
            "COALESCE(channels -> 'whatsapp' ->> 'phone_number_id', '') <> ''"
        ),
    )


def schema_downgrades() -> None:
    """schema downgrade migrations go here."""
    op.drop_index("uq_agents_whatsapp_phone_number_id", table_name="agents")


def data_upgrades() -> None:
    """Add any optional data upgrade migrations here!"""


def data_downgrades() -> None:
    """Add any optional data downgrade migrations here!"""


