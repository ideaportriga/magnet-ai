# type: ignore
"""add routing_config to ai_models

Revision ID: b7f8e9d0a1c2
Revises: a1b2c3d4e5f6
Create Date: 2026-02-05 12:00:00.000000+00:00

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
sa.ORA_JSONB = ORA_JSONB
sa.EncryptedString = EncryptedString
sa.EncryptedText = EncryptedText
sa.Text = Text


# revision identifiers, used by Alembic.
revision = "b7f8e9d0a1c2"
down_revision = "a1b2c3d4e5f6"
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
    # Add routing_config field to ai_models table for LiteLLM integration
    # This field stores: rpm, tpm, fallback_models, cache settings, priority, weight
    op.add_column(
        "ai_models",
        sa.Column(
            "routing_config",
            sa.JSON()
            .with_variant(postgresql.JSONB(astext_type=sa.Text), "cockroachdb")
            .with_variant(advanced_alchemy.types.json.ORA_JSONB(), "oracle")
            .with_variant(postgresql.JSONB(astext_type=sa.Text), "postgresql"),
            nullable=True,
            comment="Routing config: rpm, tpm, fallback_models, cache, priority, weight",
        ),
    )


def schema_downgrades() -> None:
    """schema downgrade migrations go here."""
    op.drop_column("ai_models", "routing_config")


def data_upgrades() -> None:
    """Add any optional data upgrade migrations here!"""


def data_downgrades() -> None:
    """Add any optional data downgrade migrations here!"""
