# type: ignore
"""add dynamic per-graph chunk vector tables

Revision ID: f3a7b2c1d4e5
Revises: a7b8c9d0e1f2
Create Date: 2026-04-11 12:00:00.000000+00:00

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
revision = "f3a7b2c1d4e5"
down_revision = "a7b8c9d0e1f2"
branch_labels = None
depends_on = None

DEFAULT_VECTOR_SIZE = 1536


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


def _graph_suffix(graph_id: str) -> str:
    return str(graph_id).replace("-", "_")


def _chunks_table_name(graph_id: str) -> str:
    return f"knowledge_graph_{_graph_suffix(graph_id)}_chunks"


def _vec_table_name(graph_id: str, vec_size: int) -> str:
    return f"knowledge_graph_{_graph_suffix(graph_id)}_{vec_size}_vec"


def _vec_index_prefix(graph_id: str, vec_size: int) -> str:
    return f"idx_kg_{_graph_suffix(graph_id)}_{vec_size}_vec"


def _iter_graph_ids(conn) -> list[str]:
    rows = conn.execute(
        sa.text("SELECT id::text FROM knowledge_graphs ORDER BY id::text")
    ).all()
    return [str(row[0]) for row in rows if row and row[0] is not None]


def _resolve_vector_size(conn, graph_id: str) -> int | None:
    """Read the configured embedding model for a graph and resolve its vector size.

    Returns the vector size (int) or None if no embedding model is configured.
    """
    row = conn.execute(
        sa.text(
            "SELECT settings->'indexing'->>'embedding_model' "
            "FROM knowledge_graphs WHERE id = :gid"
        ),
        {"gid": graph_id},
    ).one_or_none()

    if not row or not row[0]:
        return None

    embedding_model = str(row[0]).strip()
    if not embedding_model:
        return None

    # Look up vector_size from ai_models table
    model_row = conn.execute(
        sa.text(
            "SELECT (configs->>'vector_size')::int "
            "FROM ai_models WHERE system_name = :sn"
        ),
        {"sn": embedding_model},
    ).one_or_none()

    if model_row and model_row[0] and int(model_row[0]) > 0:
        return int(model_row[0])

    return DEFAULT_VECTOR_SIZE


def _iter_dynamic_vec_tables(conn) -> list[str]:
    """Return all per-graph vector table names (knowledge_graph_*_vec)."""
    insp = sa.inspect(conn)
    table_names = insp.get_table_names()
    return sorted(
        [
            t
            for t in table_names
            if isinstance(t, str)
            and t.startswith("knowledge_graph_")
            and t.endswith("_vec")
        ]
    )


def schema_upgrades() -> None:
    """Create per-graph chunk vector tables and copy existing embeddings."""
    bind = op.get_bind()
    existing_tables = {
        table_name
        for table_name in sa.inspect(bind).get_table_names()
        if isinstance(table_name, str)
    }

    for graph_id in _iter_graph_ids(bind):
        vec_size = _resolve_vector_size(bind, graph_id)
        if vec_size is None:
            continue

        chunks_table = _chunks_table_name(graph_id)
        if chunks_table not in existing_tables:
            continue

        vec_table = _vec_table_name(graph_id, vec_size)
        if vec_table in existing_tables:
            continue

        index_prefix = _vec_index_prefix(graph_id, vec_size)

        # Create the vector table using raw SQL (pgvector vector type)
        bind.execute(
            sa.text(
                f"""
                CREATE TABLE "{vec_table}" (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    chunk_id UUID NOT NULL
                        REFERENCES "{chunks_table}" (id) ON DELETE CASCADE,
                    content_type VARCHAR(100) NOT NULL DEFAULT 'chunk_content',
                    content TEXT,
                    vector vector({vec_size}),
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )

        # Create indexes
        bind.execute(
            sa.text(
                f'CREATE INDEX "{index_prefix}_chunk_id" ON "{vec_table}" (chunk_id)'
            )
        )
        bind.execute(
            sa.text(
                f'CREATE INDEX "{index_prefix}_chunk_ct" '
                f'ON "{vec_table}" (chunk_id, content_type)'
            )
        )

        # Copy existing vectors from chunks table
        bind.execute(
            sa.text(
                f"""
                INSERT INTO "{vec_table}" (chunk_id, content_type, content, vector)
                SELECT id, 'chunk_content',
                       COALESCE(embedded_content, content, ''),
                       content_embedding
                FROM "{chunks_table}"
                WHERE content_embedding IS NOT NULL
                """
            )
        )


def schema_downgrades() -> None:
    """Drop all per-graph vector tables."""
    bind = op.get_bind()
    for table_name in _iter_dynamic_vec_tables(bind):
        bind.execute(sa.text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE'))


def data_upgrades() -> None:
    """Add any optional data upgrade migrations here!"""


def data_downgrades() -> None:
    """Add any optional data downgrade migrations here!"""
