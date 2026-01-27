# type: ignore
"""add intelligent sync fields to kg docs

Revision ID: 219c74c3e359
Revises: a1b2c3d4e5f6
Create Date: 2026-02-03 15:59:51.096429+00:00

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
# Additional type aliases for proper migration generation
sa.Text = Text


# revision identifiers, used by Alembic.
revision = "219c74c3e359"
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


def _extract_graph_id_from_table_name(table_name: str) -> str:
    """Extract graph ID from table name: knowledge_graph_{graph_id}_docs -> {graph_id}"""
    # Remove prefix and suffix
    prefix = "knowledge_graph_"
    suffix = "_docs"
    if table_name.startswith(prefix) and table_name.endswith(suffix):
        return table_name[len(prefix) : -len(suffix)]
    return ""


def _docs_index_prefix(graph_id: str) -> str:
    """Per-graph documents index prefix (matches utils.docs_index_prefix)."""
    return f"idx_kg_{graph_id}_docs"


def schema_upgrades() -> None:
    """schema upgrade migrations go here."""
    bind = op.get_bind()
    insp = sa.inspect(bind)

    for table_name in _iter_dynamic_docs_tables(bind):
        cols = {
            c.get("name") for c in insp.get_columns(table_name) if isinstance(c, dict)
        }

        # Add intelligent sync tracking columns
        if "source_document_id" not in cols:
            op.add_column(
                table_name,
                sa.Column("source_document_id", sa.String(500), nullable=True),
            )

        if "source_modified_at" not in cols:
            op.add_column(
                table_name,
                sa.Column("source_modified_at", sa.DateTime(), nullable=True),
            )

        if "content_hash" not in cols:
            op.add_column(
                table_name,
                sa.Column("content_hash", sa.String(64), nullable=True),
            )

        # Create composite index for efficient sync lookups
        # Use short index name to stay under PostgreSQL's 63 character limit
        graph_id = _extract_graph_id_from_table_name(table_name)
        index_prefix = _docs_index_prefix(graph_id)
        index_name = f"{index_prefix}_source_doc_id"
        existing_indexes = {
            idx.get("name")
            for idx in insp.get_indexes(table_name)
            if isinstance(idx, dict)
        }
        if index_name not in existing_indexes:
            op.create_index(index_name, table_name, ["source_id", "source_document_id"])


def schema_downgrades() -> None:
    """schema downgrade migrations go here."""
    bind = op.get_bind()
    insp = sa.inspect(bind)

    for table_name in _iter_dynamic_docs_tables(bind):
        # Drop composite index
        graph_id = _extract_graph_id_from_table_name(table_name)
        index_prefix = _docs_index_prefix(graph_id)
        index_name = f"{index_prefix}_source_doc_id"
        existing_indexes = {
            idx.get("name")
            for idx in insp.get_indexes(table_name)
            if isinstance(idx, dict)
        }
        if index_name in existing_indexes:
            op.drop_index(index_name, table_name=table_name)

        # Drop columns
        cols = {
            c.get("name") for c in insp.get_columns(table_name) if isinstance(c, dict)
        }
        if "content_hash" in cols:
            op.drop_column(table_name, "content_hash")
        if "source_modified_at" in cols:
            op.drop_column(table_name, "source_modified_at")
        if "source_document_id" in cols:
            op.drop_column(table_name, "source_document_id")


def data_upgrades() -> None:
    """Add any optional data upgrade migrations here!"""


def data_downgrades() -> None:
    """Add any optional data downgrade migrations here!"""
