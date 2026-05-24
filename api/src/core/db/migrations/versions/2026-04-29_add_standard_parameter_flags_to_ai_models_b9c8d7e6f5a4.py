# type: ignore
"""add standard parameter flags to ai_models

Revision ID: b9c8d7e6f5a4
Revises: a3b4c5d6e7f8
Create Date: 2026-04-29 00:00:00.000000+00:00
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
revision = "b9c8d7e6f5a4"
down_revision = "a3b4c5d6e7f8"
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
        "ai_models",
        sa.Column(
            "supports_temperature",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
            comment="Whether the model accepts the `temperature` parameter",
        ),
    )
    op.add_column(
        "ai_models",
        sa.Column(
            "supports_top_p",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
            comment="Whether the model accepts the `top_p` parameter",
        ),
    )
    op.add_column(
        "ai_models",
        sa.Column(
            "supports_max_tokens",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
            comment="Whether the model accepts the `max_tokens` parameter",
        ),
    )


def schema_downgrades() -> None:
    """schema downgrade migrations go here."""
    op.drop_column("ai_models", "supports_max_tokens")
    op.drop_column("ai_models", "supports_top_p")
    op.drop_column("ai_models", "supports_temperature")


def data_upgrades() -> None:
    """Add any optional data upgrade migrations here!"""


def data_downgrades() -> None:
    """Add any optional data downgrade migrations here!"""
