# type: ignore
"""Drop the now-unused documents_count column from knowledge_graph_sources.

Revision ID: c9d8e7f6a5b4
Revises: b8a7c6d5e4f3
Create Date: 2026-05-18 00:00:00.000000+00:00

The cached counter is replaced by an on-read aggregation against each
graph's per-graph documents table, so this column is no longer maintained
and no longer read.
"""

from __future__ import annotations

import warnings

import sqlalchemy as sa
from advanced_alchemy.types import (
    GUID,
    ORA_JSONB,
    DateTimeUTC,
    EncryptedString,
    EncryptedText,
)
from alembic import op
from sqlalchemy import Text  # noqa: F401

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
revision = "c9d8e7f6a5b4"
down_revision = "b8a7c6d5e4f3"
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
    op.drop_column("knowledge_graph_sources", "documents_count")


def schema_downgrades() -> None:
    op.add_column(
        "knowledge_graph_sources",
        sa.Column(
            "documents_count",
            sa.Integer(),
            nullable=True,
            comment="Number of documents from this source",
        ),
    )


def data_upgrades() -> None:
    """Add any optional data upgrade migrations here!"""


def data_downgrades() -> None:
    """Add any optional data downgrade migrations here!"""
