# type: ignore
"""Backfill ``account_link_code`` columns missed by d3e4f5a6b7c8.

The model :class:`AccountLinkCode` extends ``UUIDAuditBase``, which expects
the audit pair ``created_at`` / ``updated_at`` plus advanced_alchemy's
``sa_orm_sentinel`` (used by ORM bulk-insert optimisations). The first
draft of the migration created the table without ``updated_at`` and
``sa_orm_sentinel``, so SELECTs through the ORM failed with
``UndefinedColumnError``.

Idempotent — uses ``ADD COLUMN IF NOT EXISTS``. Fresh setups already get
the columns from the (now fixed) parent migration; this one only matters
for DBs that already ran d3e4f5a6b7c8 against the broken DDL.

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-05-26 12:00:00.000000+00:00
"""

from __future__ import annotations

import warnings

from alembic import op

__all__ = ["downgrade", "upgrade", "schema_upgrades", "schema_downgrades"]

revision = "e4f5a6b7c8d9"
down_revision = "d3e4f5a6b7c8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        with op.get_context().autocommit_block():
            schema_upgrades()


def downgrade() -> None:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        with op.get_context().autocommit_block():
            schema_downgrades()


def schema_upgrades() -> None:
    op.execute(
        "ALTER TABLE account_link_code "
        "ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()"
    )
    op.execute(
        "ALTER TABLE account_link_code "
        "ADD COLUMN IF NOT EXISTS sa_orm_sentinel INTEGER NULL"
    )


def schema_downgrades() -> None:
    # Don't drop — keeps downgrade safe even if some other migration starts
    # depending on the column. Re-running upgrade is a no-op (IF NOT EXISTS).
    pass
