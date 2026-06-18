# type: ignore
"""agent conversation async fields (generation + callback)

Revision ID: c8d9e0f1a2b3
Revises: a7b8c9d0e1f2
Create Date: 2026-06-18 00:00:00.000000+00:00
"""

from __future__ import annotations

import warnings

import sqlalchemy as sa
from alembic import op
from advanced_alchemy.types import (
    DateTimeUTC,
    EncryptedString,
    EncryptedText,
    GUID,
    ORA_JSONB,
)

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
sa.ORA_JSONB = ORA_JSONB
sa.EncryptedString = EncryptedString
sa.EncryptedText = EncryptedText

# revision identifiers, used by Alembic.
revision = "c8d9e0f1a2b3"
down_revision = "a7b8c9d0e1f2"
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
    # Monotonic counter bumped on every new user message. A processing turn
    # captures the value it runs under and only persists its reply if the
    # stored value still matches — discarding superseded (stale) turns.
    op.add_column(
        "agent_conversations",
        sa.Column(
            "processing_generation",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
            comment="Monotonic turn counter for superseding in-flight processing",
        ),
    )
    op.alter_column("agent_conversations", "processing_generation", server_default="0")
    # Outbound webhook callback config for async (webhook-driven) invocation.
    op.add_column(
        "agent_conversations",
        sa.Column(
            "callback",
            sa.JSON().with_variant(ORA_JSONB, "oracle"),
            nullable=True,
            comment="Outbound webhook callback config (url, optional headers)",
        ),
    )


def schema_downgrades() -> None:
    """schema downgrade migrations go here."""
    op.drop_column("agent_conversations", "callback")
    op.drop_column("agent_conversations", "processing_generation")


def data_upgrades() -> None:
    """Add any optional data upgrade migrations here!"""


def data_downgrades() -> None:
    """Add any optional data downgrade migrations here!"""
