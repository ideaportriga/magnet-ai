# type: ignore
"""drop content_embedding column from dynamic chunk tables

Revision ID: b8d3e6f9a2c7
Revises: f3a7b2c1d4e5
Create Date: 2026-04-12 12:00:00.000000+00:00

"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

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
revision = "b8d3e6f9a2c7"
down_revision = "f3a7b2c1d4e5"
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


def _iter_chunk_tables_with_content_embedding(conn) -> list[str]:
    """Return all dynamic chunk table names that still have a content_embedding column."""
    rows = conn.execute(
        sa.text(
            "SELECT table_name FROM information_schema.columns "
            "WHERE table_name LIKE 'knowledge_graph_%_chunks' "
            "AND column_name = 'content_embedding'"
        )
    ).all()
    return sorted([str(row[0]) for row in rows if row and row[0]])


def schema_upgrades() -> None:
    """Drop content_embedding column from all dynamic chunk tables."""
    bind = op.get_bind()

    for table_name in _iter_chunk_tables_with_content_embedding(bind):
        bind.execute(
            sa.text(f'ALTER TABLE "{table_name}" DROP COLUMN content_embedding')
        )


def schema_downgrades() -> None:
    """Re-add content_embedding column to dynamic chunk tables (data is lost)."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    chunk_tables = sorted(
        t
        for t in insp.get_table_names()
        if isinstance(t, str)
        and t.startswith("knowledge_graph_")
        and t.endswith("_chunks")
    )
    for table_name in chunk_tables:
        # Check if column already exists (idempotent)
        columns = [c["name"] for c in insp.get_columns(table_name)]
        if "content_embedding" not in columns:
            bind.execute(
                sa.text(
                    f'ALTER TABLE "{table_name}" ADD COLUMN content_embedding vector'
                )
            )


def data_upgrades() -> None:
    """Add any optional data upgrade migrations here!"""


def data_downgrades() -> None:
    """Add any optional data downgrade migrations here!"""
