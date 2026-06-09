# type: ignore
"""Enable hybrid search (pgvector + tsvector + pg_trgm) for KG retrieval.

Revision ID: e1f2a3b4c5d6
Revises: d0e9f8a7b6c5
Create Date: 2026-05-25 00:00:00.000000+00:00

For every per-graph documents and chunks table this migration:

- adds a STORED generated `search_tsv` column (full-text index target),
- creates a GIN index over `search_tsv`,
- creates GIN trigram indexes (`gin_trgm_ops`) over the searchable text columns.

It also enables the `pg_trgm` extension if needed. Generated columns require
IMMUTABLE expressions, which `to_tsvector('english', ...)` satisfies, so no
data backfill is needed.
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
revision = "e1f2a3b4c5d6"
down_revision = "d0e9f8a7b6c5"
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


def _add_search_tsv(
    table_name: str, text_cols: tuple[str, str], existing_cols: set[str]
) -> None:
    """Add the STORED generated tsvector column over (col_a, col_b)."""
    if "search_tsv" in existing_cols:
        return
    a, b = text_cols
    op.execute(
        sa.text(
            f"ALTER TABLE {table_name} "
            f"ADD COLUMN search_tsv tsvector GENERATED ALWAYS AS ("
            f"to_tsvector('english', coalesce({a}, '') || ' ' || coalesce({b}, ''))"
            f") STORED"
        )
    )


def _create_gin_index(
    insp, table_name: str, index_name: str, sql_definition: str
) -> None:
    existing = {
        idx.get("name") for idx in insp.get_indexes(table_name) if isinstance(idx, dict)
    }
    if index_name in existing:
        return
    op.execute(sa.text(sql_definition))


def schema_upgrades() -> None:
    bind = op.get_bind()

    # 1) Extension. autocommit_block lets this run outside a transaction.
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))

    # 2) Per-graph documents tables.
    insp = sa.inspect(bind)
    for table_name in _iter_dynamic_tables(bind, "_docs"):
        existing_cols = {
            c.get("name") for c in insp.get_columns(table_name) if isinstance(c, dict)
        }
        _add_search_tsv(table_name, ("title", "summary"), existing_cols)

        graph_id = _graph_id_from_table_name(table_name, "_docs")
        prefix = _docs_index_prefix(graph_id)

        # Re-inspect after the ALTER above (column list changed).
        insp = sa.inspect(bind)

        _create_gin_index(
            insp,
            table_name,
            f"{prefix}search_tsv",
            f"CREATE INDEX IF NOT EXISTS {prefix}search_tsv "
            f"ON {table_name} USING GIN (search_tsv)",
        )
        _create_gin_index(
            insp,
            table_name,
            f"{prefix}summary_trgm",
            f"CREATE INDEX IF NOT EXISTS {prefix}summary_trgm "
            f"ON {table_name} USING GIN (summary gin_trgm_ops)",
        )
        _create_gin_index(
            insp,
            table_name,
            f"{prefix}title_trgm",
            f"CREATE INDEX IF NOT EXISTS {prefix}title_trgm "
            f"ON {table_name} USING GIN (title gin_trgm_ops)",
        )

    # 3) Per-graph chunks tables.
    insp = sa.inspect(bind)
    for table_name in _iter_dynamic_tables(bind, "_chunks"):
        existing_cols = {
            c.get("name") for c in insp.get_columns(table_name) if isinstance(c, dict)
        }
        _add_search_tsv(table_name, ("title", "content"), existing_cols)

        graph_id = _graph_id_from_table_name(table_name, "_chunks")
        prefix = _chunks_index_prefix(graph_id)

        insp = sa.inspect(bind)

        _create_gin_index(
            insp,
            table_name,
            f"{prefix}search_tsv",
            f"CREATE INDEX IF NOT EXISTS {prefix}search_tsv "
            f"ON {table_name} USING GIN (search_tsv)",
        )
        _create_gin_index(
            insp,
            table_name,
            f"{prefix}content_trgm",
            f"CREATE INDEX IF NOT EXISTS {prefix}content_trgm "
            f"ON {table_name} USING GIN (content gin_trgm_ops)",
        )
        _create_gin_index(
            insp,
            table_name,
            f"{prefix}title_trgm",
            f"CREATE INDEX IF NOT EXISTS {prefix}title_trgm "
            f"ON {table_name} USING GIN (title gin_trgm_ops)",
        )


def schema_downgrades() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    for table_name in _iter_dynamic_tables(bind, "_docs"):
        graph_id = _graph_id_from_table_name(table_name, "_docs")
        prefix = _docs_index_prefix(graph_id)
        for ix in (
            f"{prefix}title_trgm",
            f"{prefix}summary_trgm",
            f"{prefix}search_tsv",
        ):
            op.execute(sa.text(f"DROP INDEX IF EXISTS {ix}"))
        cols = {
            c.get("name") for c in insp.get_columns(table_name) if isinstance(c, dict)
        }
        if "search_tsv" in cols:
            op.execute(sa.text(f"ALTER TABLE {table_name} DROP COLUMN search_tsv"))

    for table_name in _iter_dynamic_tables(bind, "_chunks"):
        graph_id = _graph_id_from_table_name(table_name, "_chunks")
        prefix = _chunks_index_prefix(graph_id)
        for ix in (
            f"{prefix}title_trgm",
            f"{prefix}content_trgm",
            f"{prefix}search_tsv",
        ):
            op.execute(sa.text(f"DROP INDEX IF EXISTS {ix}"))
        cols = {
            c.get("name") for c in insp.get_columns(table_name) if isinstance(c, dict)
        }
        if "search_tsv" in cols:
            op.execute(sa.text(f"ALTER TABLE {table_name} DROP COLUMN search_tsv"))

    # We deliberately do not drop the pg_trgm extension; other features may rely on it.


def data_upgrades() -> None:
    """Add any optional data upgrade migrations here!"""


def data_downgrades() -> None:
    """Add any optional data downgrade migrations here!"""
