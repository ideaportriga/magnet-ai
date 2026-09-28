# type: ignore
"""add cache write pricing and pricing scheme to ai_models

Revision ID: c7e9a1b3d5f4
Revises: c5d6e7f8a9b0
Create Date: 2026-09-24 00:00:00.000000+00:00
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
revision = "c7e9a1b3d5f4"
down_revision = "c5d6e7f8a9b0"
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
            "price_cache_write",
            sa.String(20),
            nullable=True,
            comment="Price per cache write input unit",
        ),
    )
    op.add_column(
        "ai_models",
        sa.Column(
            "price_long_context_cache_write",
            sa.String(20),
            nullable=True,
            comment="Price per cache write input unit when input exceeds long-context threshold",
        ),
    )
    op.add_column(
        "ai_models",
        sa.Column(
            "price_cache_write_1h",
            sa.String(20),
            nullable=True,
            comment="Price per 1-hour cache write input unit",
        ),
    )
    op.add_column(
        "ai_models",
        sa.Column(
            "price_long_context_cache_write_1h",
            sa.String(20),
            nullable=True,
            comment="Price per 1-hour cache write input unit when input exceeds long-context threshold",
        ),
    )
    op.add_column(
        "ai_models",
        sa.Column(
            "price_scheme",
            sa.String(20),
            nullable=True,
            comment="Pricing scheme: basic, openai, anthropic",
        ),
    )


def schema_downgrades() -> None:
    """schema downgrade migrations go here."""
    op.drop_column("ai_models", "price_scheme")
    op.drop_column("ai_models", "price_long_context_cache_write_1h")
    op.drop_column("ai_models", "price_cache_write_1h")
    op.drop_column("ai_models", "price_long_context_cache_write")
    op.drop_column("ai_models", "price_cache_write")


def data_upgrades() -> None:
    """Add any optional data upgrade migrations here!"""


def data_downgrades() -> None:
    """Add any optional data downgrade migrations here!"""
