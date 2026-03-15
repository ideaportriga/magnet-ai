# type: ignore
"""add dynamic kg edges tables

Revision ID: a7b8c9d0e1f2
Revises: 6f1e2d3c4b5a
Create Date: 2026-03-14 12:00:00.000000+00:00

"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

import sqlalchemy as sa
from advanced_alchemy.types import (
    DateTimeUTC,
    EncryptedString,
    EncryptedText,
    GUID,
    ORA_JSONB,
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
sa.Text = Text


# revision identifiers, used by Alembic.
revision = "a7b8c9d0e1f2"
down_revision = "6f1e2d3c4b5a"
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


def _edges_table_name(graph_id: str) -> str:
    return f"knowledge_graph_{_graph_suffix(graph_id)}_edges"


def _edges_index_prefix(graph_id: str) -> str:
    return f"idx_kg_{_graph_suffix(graph_id)}_edges"


def _iter_graph_ids(conn) -> list[str]:
    rows = conn.execute(
        sa.text("SELECT id::text FROM knowledge_graphs ORDER BY id::text")
    ).all()
    return [str(row[0]) for row in rows if row and row[0] is not None]


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


def schema_upgrades() -> None:
    """schema upgrade migrations go here."""
    bind = op.get_bind()
    existing_tables = {
        table_name
        for table_name in sa.inspect(bind).get_table_names()
        if isinstance(table_name, str)
    }

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


def schema_downgrades() -> None:
    """schema downgrade migrations go here."""
    for table_name in _iter_dynamic_edges_tables(op.get_bind()):
        op.drop_table(table_name)


def data_upgrades() -> None:
    """Add any optional data upgrade migrations here!"""


def data_downgrades() -> None:
    """Add any optional data downgrade migrations here!"""
