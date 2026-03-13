# type: ignore
"""add dynamic kg entities tables

Revision ID: 6f1e2d3c4b5a
Revises: c4d5e6f7a8b9
Create Date: 2026-03-11 12:00:00.000000+00:00

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
revision = "6f1e2d3c4b5a"
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


def schema_upgrades() -> None:
    """schema upgrade migrations go here."""
    bind = op.get_bind()
    existing_tables = {
        table_name
        for table_name in sa.inspect(bind).get_table_names()
        if isinstance(table_name, str)
    }

    for graph_id in _iter_graph_ids(bind):
        table_name = _entities_table_name(graph_id)
        if table_name not in existing_tables:
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
                    "source_document_ids",
                    postgresql.JSONB(astext_type=sa.Text()),
                    nullable=False,
                    server_default=sa.text("'[]'::jsonb"),
                ),
                sa.Column(
                    "source_chunk_ids",
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
            existing_tables.add(table_name)
            existing_indexes: set[str | None] = set()
        else:
            existing_columns = {
                column.get("name")
                for column in sa.inspect(bind).get_columns(table_name)
                if isinstance(column, dict)
            }

            if "normalized_record_identifier" not in existing_columns:
                op.add_column(
                    table_name,
                    sa.Column(
                        "normalized_record_identifier",
                        sa.String(length=500),
                        nullable=False,
                        server_default="",
                    ),
                )

            if "identifier_aliases" not in existing_columns:
                op.add_column(
                    table_name,
                    sa.Column(
                        "identifier_aliases",
                        postgresql.JSONB(astext_type=sa.Text()),
                        nullable=False,
                        server_default=sa.text("'[]'::jsonb"),
                    ),
                )

            if "source_document_ids" not in existing_columns:
                op.add_column(
                    table_name,
                    sa.Column(
                        "source_document_ids",
                        postgresql.JSONB(astext_type=sa.Text()),
                        nullable=False,
                        server_default=sa.text("'[]'::jsonb"),
                    ),
                )

            if "source_chunk_ids" not in existing_columns:
                op.add_column(
                    table_name,
                    sa.Column(
                        "source_chunk_ids",
                        postgresql.JSONB(astext_type=sa.Text()),
                        nullable=False,
                        server_default=sa.text("'[]'::jsonb"),
                    ),
                )

            existing_indexes = {
                idx.get("name")
                for idx in sa.inspect(bind).get_indexes(table_name)
                if isinstance(idx, dict)
            }

        index_prefix = _entities_index_prefix(graph_id)
        entity_index_name = f"{index_prefix}_entity"
        legacy_unique_index_name = f"{index_prefix}_erid_uq"
        unique_index_name = f"{index_prefix}_nrid_uq"
        gin_index_name = f"{index_prefix}_cols_gin"

        op.execute(
            sa.text(
                f"""
                UPDATE {table_name}
                SET normalized_record_identifier = LOWER(BTRIM(record_identifier))
                WHERE COALESCE(normalized_record_identifier, '') = ''
                """
            )
        )

        if entity_index_name not in existing_indexes:
            op.create_index(entity_index_name, table_name, ["entity"])
        if legacy_unique_index_name in existing_indexes:
            op.drop_index(legacy_unique_index_name, table_name=table_name)
        if unique_index_name not in existing_indexes:
            op.create_index(
                unique_index_name,
                table_name,
                ["entity", "normalized_record_identifier"],
                unique=True,
            )
        if gin_index_name not in existing_indexes:
            op.create_index(
                gin_index_name,
                table_name,
                ["column_values"],
                postgresql_using="gin",
            )


def schema_downgrades() -> None:
    """schema downgrade migrations go here."""
    for table_name in _iter_dynamic_entities_tables(op.get_bind()):
        op.drop_table(table_name)


def data_upgrades() -> None:
    """Add any optional data upgrade migrations here!"""


def data_downgrades() -> None:
    """Add any optional data downgrade migrations here!"""
