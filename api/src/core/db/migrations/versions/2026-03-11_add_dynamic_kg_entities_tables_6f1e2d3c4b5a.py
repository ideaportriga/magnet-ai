# type: ignore
"""add dynamic kg entities/edges tables, state columns

Revision ID: c9d0e1f2a3b4
Revises: c4d5e6f7a8b9
Create Date: 2026-03-11 12:00:00.000000+00:00

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
from sqlalchemy.dialects.postgresql import JSONB

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
revision = "c9d0e1f2a3b4"
down_revision = "c4d5e6f7a8b9"
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


def _graph_suffix(graph_id: str) -> str:
    return str(graph_id).replace("-", "_")


def _entities_table_name(graph_id: str) -> str:
    return f"knowledge_graph_{_graph_suffix(graph_id)}_entities"


def _entities_index_prefix(graph_id: str) -> str:
    # Keep generated names under PostgreSQL's 63 character limit.
    return f"idx_kg_{_graph_suffix(graph_id)}_entities"


def _edges_table_name(graph_id: str) -> str:
    return f"knowledge_graph_{_graph_suffix(graph_id)}_edges"


def _edges_index_prefix(graph_id: str) -> str:
    return f"idx_kg_{_graph_suffix(graph_id)}_edges"


def _iter_graph_ids(conn) -> list[str]:
    rows = conn.execute(
        sa.text("SELECT id::text FROM knowledge_graphs ORDER BY id::text")
    ).all()
    return [str(row[0]) for row in rows if row and row[0] is not None]


def _iter_dynamic_entities_tables(conn) -> list[str]:
    insp = sa.inspect(conn)
    table_names = insp.get_table_names()
    return sorted(
        [
            table_name
            for table_name in table_names
            if isinstance(table_name, str)
            and table_name.startswith("knowledge_graph_")
            and table_name.endswith("_entities")
        ]
    )


def _iter_dynamic_edges_tables(conn) -> list[str]:
    insp = sa.inspect(conn)
    table_names = insp.get_table_names()
    return sorted(
        [
            table_name
            for table_name in table_names
            if isinstance(table_name, str)
            and table_name.startswith("knowledge_graph_")
            and table_name.endswith("_edges")
        ]
    )


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
    existing_tables = {
        table_name
        for table_name in sa.inspect(bind).get_table_names()
        if isinstance(table_name, str)
    }
    insp = sa.inspect(bind)

    # --- 1. Create per-graph entities tables ---
    for graph_id in _iter_graph_ids(bind):
        table_name = _entities_table_name(graph_id)
        if table_name in existing_tables:
            continue

        op.create_table(
            table_name,
            sa.Column(
                "id",
                sa.GUID(),
                primary_key=True,
                nullable=False,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("entity", sa.String(length=255), nullable=False),
            sa.Column("record_identifier", sa.String(length=500), nullable=False),
            sa.Column(
                "normalized_record_identifier",
                sa.String(length=500),
                nullable=False,
                server_default="",
            ),
            sa.Column(
                "column_values",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default=sa.text("'{}'::jsonb"),
            ),
            sa.Column(
                "identifier_aliases",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default=sa.text("'[]'::jsonb"),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=True,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=True,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
        )

        index_prefix = _entities_index_prefix(graph_id)
        op.create_index(f"{index_prefix}_entity", table_name, ["entity"])
        op.create_index(
            f"{index_prefix}_nrid_uq",
            table_name,
            ["entity", "normalized_record_identifier"],
            unique=True,
        )
        op.create_index(
            f"{index_prefix}_cols_gin",
            table_name,
            ["column_values"],
            postgresql_using="gin",
        )

    # --- 2. Create per-graph edges tables ---
    for graph_id in _iter_graph_ids(bind):
        edges_table = _edges_table_name(graph_id)
        if edges_table in existing_tables:
            continue

        op.create_table(
            edges_table,
            sa.Column(
                "id",
                sa.GUID(),
                primary_key=True,
                nullable=False,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("source_node_id", sa.GUID(), nullable=False),
            sa.Column(
                "source_node_type",
                sa.String(length=50),
                nullable=False,
                server_default=sa.text("'entity'"),
            ),
            sa.Column("target_node_id", sa.GUID(), nullable=False),
            sa.Column("target_node_type", sa.String(length=50), nullable=False),
            sa.Column(
                "label",
                sa.String(length=255),
                nullable=False,
                server_default=sa.text("''"),
            ),
            sa.Column(
                "metadata",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
                server_default=sa.text("'{}'::jsonb"),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=True,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=True,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
        )

        index_prefix = _edges_index_prefix(graph_id)
        op.create_index(
            f"{index_prefix}_src",
            edges_table,
            ["source_node_id", "source_node_type"],
        )
        op.create_index(
            f"{index_prefix}_tgt",
            edges_table,
            ["target_node_id", "target_node_type"],
        )
        op.create_index(
            f"{index_prefix}_src_tgt_uq",
            edges_table,
            [
                "source_node_id",
                "source_node_type",
                "target_node_id",
                "target_node_type",
            ],
            unique=True,
        )

    # --- 3. Add state column to knowledge_graphs ---
    kg_cols = {
        c.get("name")
        for c in insp.get_columns("knowledge_graphs")
        if isinstance(c, dict)
    }
    if "state" not in kg_cols:
        op.add_column(
            "knowledge_graphs",
            sa.Column(
                "state",
                JSONB,
                nullable=True,
                comment="Process states for graph operations (extraction status, sync progress, etc.)",
            ),
        )

    # --- 4. Add pipeline_state column to per-graph docs tables ---
    for docs_table in _iter_dynamic_docs_tables(bind):
        cols = {
            c.get("name") for c in insp.get_columns(docs_table) if isinstance(c, dict)
        }
        if "pipeline_state" not in cols:
            op.add_column(
                docs_table,
                sa.Column("pipeline_state", JSONB, nullable=True),
            )


def schema_downgrades() -> None:
    """schema downgrade migrations go here."""
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # --- 4. Drop pipeline_state from docs tables ---
    for docs_table in _iter_dynamic_docs_tables(bind):
        cols = {
            c.get("name") for c in insp.get_columns(docs_table) if isinstance(c, dict)
        }
        if "pipeline_state" in cols:
            op.drop_column(docs_table, "pipeline_state")

    # --- 3. Drop state column from knowledge_graphs ---
    kg_cols = {
        c.get("name")
        for c in insp.get_columns("knowledge_graphs")
        if isinstance(c, dict)
    }
    if "state" in kg_cols:
        op.drop_column("knowledge_graphs", "state")

    # --- 2. Drop edges tables ---
    for table_name in _iter_dynamic_edges_tables(bind):
        op.drop_table(table_name)

    # --- 1. Drop entities tables ---
    for table_name in _iter_dynamic_entities_tables(bind):
        op.drop_table(table_name)


def data_upgrades() -> None:
    """Add any optional data upgrade migrations here!"""


def data_downgrades() -> None:
    """Add any optional data downgrade migrations here!"""
