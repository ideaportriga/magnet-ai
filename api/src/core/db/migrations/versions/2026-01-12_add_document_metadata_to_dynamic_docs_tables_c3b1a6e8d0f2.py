# type: ignore
"""add document metadata to dynamic docs tables

Revision ID: c3b1a6e8d0f2
Revises: 39837e80ce55
Create Date: 2026-01-06 00:00:00.000000+00:00

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
# Additional type aliases for proper migration generation
sa.Text = Text


# revision identifiers, used by Alembic.
revision = "c3b1a6e8d0f2"
down_revision = "39837e80ce55"
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


def _iter_dynamic_docs_tables(conn) -> list[str]:
    """Return all per-graph documents table names (knowledge_graph_*_docs)."""
    insp = sa.inspect(conn)
    table_names = insp.get_table_names()
    return sorted(
        [
            t
            for t in table_names
            if isinstance(t, str)
            and t.startswith("knowledge_graph_")
            and t.endswith("_docs")
        ]
    )


def schema_upgrades() -> None:
    """schema upgrade migrations go here."""
    bind = op.get_bind()
    insp = sa.inspect(bind)

    for table_name in _iter_dynamic_docs_tables(bind):
        cols = {
            c.get("name") for c in insp.get_columns(table_name) if isinstance(c, dict)
        }
        if "metadata" not in cols:
            op.add_column(
                table_name,
                sa.Column(
                    "metadata",
                    postgresql.JSONB(astext_type=sa.Text),
                    nullable=True,
                    server_default=sa.text("'{}'::jsonb"),
                ),
            )
        if "content_plaintext" not in cols:
            op.add_column(
                table_name, sa.Column("content_plaintext", sa.Text(), nullable=True)
            )


def schema_downgrades() -> None:
    """schema downgrade migrations go here."""
    bind = op.get_bind()
    insp = sa.inspect(bind)

    for table_name in _iter_dynamic_docs_tables(bind):
        cols = {
            c.get("name") for c in insp.get_columns(table_name) if isinstance(c, dict)
        }
        if "metadata" in cols:
            op.drop_column(table_name, "metadata")
        if "content_plaintext" in cols:
            op.drop_column(table_name, "content_plaintext")


def data_upgrades() -> None:
    """Add any optional data upgrade migrations here!"""


def data_downgrades() -> None:
    """Add any optional data downgrade migrations here!"""
