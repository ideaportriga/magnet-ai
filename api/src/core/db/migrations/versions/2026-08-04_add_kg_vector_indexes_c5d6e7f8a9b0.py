# type: ignore
"""Add HNSW vector indexes to per-graph KG documents and chunks tables.

Revision ID: c5d6e7f8a9b0
Revises: b4c5d6e7f8a9
Create Date: 2026-08-04 00:00:00.000000+00:00

KG vector search orders by `embedding <=> :qvec`, but no vector index was
ever created on the per-graph tables, so every search was a sequential scan
over all rows. This migration creates an HNSW cosine index on
`docs.summary_embedding` and `chunks.content_embedding` for every existing
per-graph table, matching what
KnowledgeGraphDocumentService.create_table/KnowledgeGraphChunkService.create_table
now create for new graphs.

Columns whose vector type is unbounded or wider than 2000 dimensions are
skipped — pgvector indexes support at most 2000 dimensions. Index builds run
in the autocommit block; large graphs may take a while to index.
"""

from __future__ import annotations

import re
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
revision = "c5d6e7f8a9b0"
down_revision = "b4c5d6e7f8a9"
branch_labels = None
depends_on = None

# pgvector HNSW/IVFFlat indexes support at most 2000 dimensions.
MAX_INDEXABLE_DIMS = 2000


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


def _iter_dynamic_tables(conn, suffix: str) -> list[str]:
    insp = sa.inspect(conn)
    return sorted(
        t
        for t in insp.get_table_names()
        if isinstance(t, str)
        and t.startswith("knowledge_graph_")
        and t.endswith(suffix)
    )


def _graph_id_from_table_name(table_name: str, suffix: str) -> str:
    prefix = "knowledge_graph_"
    if table_name.startswith(prefix) and table_name.endswith(suffix):
        return table_name[len(prefix) : -len(suffix)]
    return ""


def _docs_index_prefix(graph_id: str) -> str:
    # Matches utils.docs_index_prefix(): trailing underscore included.
    return f"idx_kg_{graph_id}_docs_"


def _chunks_index_prefix(graph_id: str) -> str:
    # Matches utils.chunks_index_prefix(): trailing underscore included.
    return f"idx_kg_{graph_id}_chunks_"


def _vector_dims(bind, table_name: str, column: str) -> int | None:
    """Return the declared vector dimension of a column, or None if unbounded
    or not a vector column."""
    formatted = bind.execute(
        sa.text(
            "SELECT format_type(a.atttypid, a.atttypmod) "
            "FROM pg_attribute a "
            "WHERE a.attrelid = to_regclass(:t) "
            "AND a.attname = :c AND NOT a.attisdropped"
        ),
        {"t": table_name, "c": column},
    ).scalar()
    if not formatted:
        return None
    match = re.fullmatch(r"vector\((\d+)\)", str(formatted))
    return int(match.group(1)) if match else None


def _create_hnsw_index(insp, table_name: str, index_name: str, column: str) -> None:
    existing = {
        idx.get("name") for idx in insp.get_indexes(table_name) if isinstance(idx, dict)
    }
    if index_name in existing:
        return
    op.execute(
        sa.text(
            f"CREATE INDEX IF NOT EXISTS {index_name} "
            f"ON {table_name} USING hnsw ({column} vector_cosine_ops) "
            f"WITH (m = 16, ef_construction = 64)"
        )
    )


def schema_upgrades() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    for table_name in _iter_dynamic_tables(bind, "_docs"):
        dims = _vector_dims(bind, table_name, "summary_embedding")
        if dims is None or dims > MAX_INDEXABLE_DIMS:
            continue
        graph_id = _graph_id_from_table_name(table_name, "_docs")
        prefix = _docs_index_prefix(graph_id)
        _create_hnsw_index(insp, table_name, f"{prefix}emb_hnsw", "summary_embedding")

    for table_name in _iter_dynamic_tables(bind, "_chunks"):
        dims = _vector_dims(bind, table_name, "content_embedding")
        if dims is None or dims > MAX_INDEXABLE_DIMS:
            continue
        graph_id = _graph_id_from_table_name(table_name, "_chunks")
        prefix = _chunks_index_prefix(graph_id)
        _create_hnsw_index(insp, table_name, f"{prefix}emb_hnsw", "content_embedding")


def schema_downgrades() -> None:
    bind = op.get_bind()

    for table_name in _iter_dynamic_tables(bind, "_docs"):
        graph_id = _graph_id_from_table_name(table_name, "_docs")
        prefix = _docs_index_prefix(graph_id)
        op.execute(sa.text(f"DROP INDEX IF EXISTS {prefix}emb_hnsw"))

    for table_name in _iter_dynamic_tables(bind, "_chunks"):
        graph_id = _graph_id_from_table_name(table_name, "_chunks")
        prefix = _chunks_index_prefix(graph_id)
        op.execute(sa.text(f"DROP INDEX IF EXISTS {prefix}emb_hnsw"))


def data_upgrades() -> None:
    """Add any optional data upgrade migrations here!"""


def data_downgrades() -> None:
    """Add any optional data downgrade migrations here!"""
