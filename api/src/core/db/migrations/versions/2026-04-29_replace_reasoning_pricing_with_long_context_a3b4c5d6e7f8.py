# type: ignore
"""replace reasoning pricing with long-context pricing on ai_models

Revision ID: a3b4c5d6e7f8
Revises: f1e2d3c4b5a6
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
revision = "a3b4c5d6e7f8"
down_revision = "f1e2d3c4b5a6"
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
    op.drop_column("ai_models", "price_reasoning")
    op.drop_column("ai_models", "price_reasoning_output_unit_count")

    op.add_column(
        "ai_models",
        sa.Column(
            "price_long_context_threshold",
            sa.Integer(),
            nullable=True,
            comment="Input token threshold above which long-context pricing applies",
        ),
    )
    op.add_column(
        "ai_models",
        sa.Column(
            "price_long_context_input",
            sa.String(20),
            nullable=True,
            comment="Price per input unit when input exceeds long-context threshold",
        ),
    )
    op.add_column(
        "ai_models",
        sa.Column(
            "price_long_context_cached",
            sa.String(20),
            nullable=True,
            comment="Price per cached input unit when input exceeds long-context threshold",
        ),
    )
    op.add_column(
        "ai_models",
        sa.Column(
            "price_long_context_output",
            sa.String(20),
            nullable=True,
            comment="Price per output unit when input exceeds long-context threshold",
        ),
    )


def schema_downgrades() -> None:
    """schema downgrade migrations go here."""
    op.drop_column("ai_models", "price_long_context_output")
    op.drop_column("ai_models", "price_long_context_cached")
    op.drop_column("ai_models", "price_long_context_input")
    op.drop_column("ai_models", "price_long_context_threshold")

    op.add_column(
        "ai_models",
        sa.Column(
            "price_reasoning_output_unit_count",
            sa.Integer(),
            nullable=True,
            comment="Reasoning output unit count for pricing",
        ),
    )
    op.add_column(
        "ai_models",
        sa.Column(
            "price_reasoning",
            sa.String(20),
            nullable=True,
            comment="Price per reasoning output unit",
        ),
    )


def data_upgrades() -> None:
    """Add any optional data upgrade migrations here!"""


def data_downgrades() -> None:
    """Add any optional data downgrade migrations here!"""
