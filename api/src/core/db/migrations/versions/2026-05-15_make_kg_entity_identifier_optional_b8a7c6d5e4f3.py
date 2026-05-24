# type: ignore
"""Make per-graph entity identifier columns nullable to support optional primary identifier.

Revision ID: b8a7c6d5e4f3
Revises: a1b2c3d4e5f7
Create Date: 2026-05-15 00:00:00.000000+00:00

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
revision = "b8a7c6d5e4f3"
down_revision = "a1b2c3d4e5f7"
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
    """Drop NOT NULL from record_identifier columns on every per-graph entities table.

    The existing UNIQUE index on ``(entity, normalized_record_identifier)`` uses
    Postgres' default ``NULLS DISTINCT`` semantics, so multiple NULL rows under
    the same entity are allowed — exactly what we want for entity types whose
    extraction definition does not designate a primary identifier.
    """
    bind = op.get_bind()
    for table_name in _iter_dynamic_entities_tables(bind):
        op.execute(
            sa.text(
                f'ALTER TABLE "{table_name}" '
                "ALTER COLUMN record_identifier DROP NOT NULL"
            )
        )
        op.execute(
            sa.text(
                f'ALTER TABLE "{table_name}" '
                "ALTER COLUMN normalized_record_identifier DROP NOT NULL"
            )
        )


def schema_downgrades() -> None:
    """Best-effort restore of NOT NULL on the identifier columns.

    Coerces any NULL rows to empty strings first so the constraint can be
    re-applied. Production downgrade is unlikely; this path exists for
    dev/test parity.
    """
    bind = op.get_bind()
    for table_name in _iter_dynamic_entities_tables(bind):
        op.execute(
            sa.text(
                f'UPDATE "{table_name}" '
                "SET record_identifier = '' WHERE record_identifier IS NULL"
            )
        )
        op.execute(
            sa.text(
                f'UPDATE "{table_name}" '
                "SET normalized_record_identifier = '' "
                "WHERE normalized_record_identifier IS NULL"
            )
        )
        op.execute(
            sa.text(
                f'ALTER TABLE "{table_name}" '
                "ALTER COLUMN record_identifier SET NOT NULL"
            )
        )
        op.execute(
            sa.text(
                f'ALTER TABLE "{table_name}" '
                "ALTER COLUMN normalized_record_identifier SET NOT NULL"
            )
        )


def data_upgrades() -> None:
    """Add any optional data upgrade migrations here!"""


def data_downgrades() -> None:
    """Add any optional data downgrade migrations here!"""
