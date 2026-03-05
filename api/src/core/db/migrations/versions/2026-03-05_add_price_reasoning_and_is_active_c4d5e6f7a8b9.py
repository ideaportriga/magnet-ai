# type: ignore
"""add price_reasoning, price_reasoning_output_unit_count, and is_active to ai_models

Revision ID: c4d5e6f7a8b9
Revises: 2a60f36c53f8
Create Date: 2026-03-05 10:00:00.000000+00:00

"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

import sqlalchemy as sa
from alembic import op
from advanced_alchemy.types import (
    EncryptedString,
    EncryptedText,
    GUID,
    ORA_JSONB,
    DateTimeUTC,
)
from sqlalchemy import Text  # noqa: F401

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
sa.ORA_JSONB = ORA_JSONB
sa.EncryptedString = EncryptedString
sa.EncryptedText = EncryptedText
sa.Text = Text


# revision identifiers, used by Alembic.
revision = "c4d5e6f7a8b9"
down_revision = "2a60f36c53f8"
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
    # Add price_reasoning field for reasoning-output pricing (o1, o3, Claude extended thinking)
    op.add_column(
        "ai_models",
        sa.Column(
            "price_reasoning",
            sa.String(20),
            nullable=True,
            comment="Price per reasoning output unit",
        ),
    )

    # Add price_reasoning_output_unit_count for reasoning pricing units
    op.add_column(
        "ai_models",
        sa.Column(
            "price_reasoning_output_unit_count",
            sa.Integer(),
            nullable=True,
            comment="Reasoning output unit count for pricing",
        ),
    )

    # Add is_active flag for soft-disabling models
    op.add_column(
        "ai_models",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
            comment="Whether the model is active and available for use",
        ),
    )


def schema_downgrades() -> None:
    """schema downgrade migrations go here."""
    op.drop_column("ai_models", "is_active")
    op.drop_column("ai_models", "price_reasoning_output_unit_count")
    op.drop_column("ai_models", "price_reasoning")


def data_upgrades() -> None:
    """Add any optional data upgrade migrations here!"""


def data_downgrades() -> None:
    """Add any optional data downgrade migrations here!"""
