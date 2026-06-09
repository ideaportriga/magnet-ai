# type: ignore
"""Drop fuzzy (pg_trgm) search from KG hybrid retrieval.

Revision ID: b4c5d6e7f8a9
Revises: a3b4c5d6e7f9
Create Date: 2026-06-05 00:00:00.000000+00:00

Fuzzy search (pg_trgm ``word_similarity`` / ``<%``) was the slow leg of KG
hybrid retrieval and is being removed. The ``"keyword"`` ("Full Text + Fuzzy")
search method is gone and ``"hybrid"`` is now Vector + Full Text only.

For every per-graph documents and chunks table this migration drops the GIN
trigram indexes (``gin_trgm_ops``). It also remaps any stored
``searchMethod = "keyword"`` tool config to ``"full_text"`` so existing graphs
keep returning results.

Notes:
- The ``search_tsv`` (full-text) GIN indexes are kept.
- The ``pg_trgm`` extension is intentionally NOT dropped: other DB objects may
  rely on it, and dropping it is global and irreversible-by-accident.
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
revision = "b4c5d6e7f8a9"
down_revision = "a3b4c5d6e7f9"
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


def schema_upgrades() -> None:
    """Drop the per-graph pg_trgm GIN indexes (keep search_tsv + extension)."""
    bind = op.get_bind()

    for table_name in _iter_dynamic_tables(bind, "_docs"):
        graph_id = _graph_id_from_table_name(table_name, "_docs")
        prefix = _docs_index_prefix(graph_id)
        for ix in (f"{prefix}summary_trgm", f"{prefix}title_trgm"):
            op.execute(sa.text(f"DROP INDEX IF EXISTS {ix}"))

    for table_name in _iter_dynamic_tables(bind, "_chunks"):
        graph_id = _graph_id_from_table_name(table_name, "_chunks")
        prefix = _chunks_index_prefix(graph_id)
        for ix in (f"{prefix}content_trgm", f"{prefix}title_trgm"):
            op.execute(sa.text(f"DROP INDEX IF EXISTS {ix}"))


def schema_downgrades() -> None:
    """Recreate the pg_trgm GIN indexes (extension is still installed)."""
    bind = op.get_bind()

    # Ensure the extension exists in case it was removed out-of-band.
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))

    for table_name in _iter_dynamic_tables(bind, "_docs"):
        graph_id = _graph_id_from_table_name(table_name, "_docs")
        prefix = _docs_index_prefix(graph_id)
        op.execute(
            sa.text(
                f"CREATE INDEX IF NOT EXISTS {prefix}summary_trgm "
                f"ON {table_name} USING GIN (summary gin_trgm_ops)"
            )
        )
        op.execute(
            sa.text(
                f"CREATE INDEX IF NOT EXISTS {prefix}title_trgm "
                f"ON {table_name} USING GIN (title gin_trgm_ops)"
            )
        )

    for table_name in _iter_dynamic_tables(bind, "_chunks"):
        graph_id = _graph_id_from_table_name(table_name, "_chunks")
        prefix = _chunks_index_prefix(graph_id)
        op.execute(
            sa.text(
                f"CREATE INDEX IF NOT EXISTS {prefix}content_trgm "
                f"ON {table_name} USING GIN (content gin_trgm_ops)"
            )
        )
        op.execute(
            sa.text(
                f"CREATE INDEX IF NOT EXISTS {prefix}title_trgm "
                f"ON {table_name} USING GIN (title gin_trgm_ops)"
            )
        )


def data_upgrades() -> None:
    """Remap any stored ``searchMethod = "keyword"`` tool config to ``"full_text"``."""
    conn = op.get_bind()

    for tool in ("retrieveChunks", "findDocumentsBySummarySimilarity"):
        conn.execute(
            sa.text(
                f"""
                UPDATE knowledge_graphs
                SET settings = jsonb_set(
                    settings,
                    '{{retrieval_tools,{tool},searchMethod}}',
                    '"full_text"'
                )
                WHERE settings IS NOT NULL
                  AND settings->'retrieval_tools'->'{tool}'->>'searchMethod'
                      = 'keyword'
                """
            )
        )


def data_downgrades() -> None:
    """No-op: ``"full_text"`` is a valid method and we cannot distinguish
    remapped configs from values set intentionally, so we do not revert them."""
