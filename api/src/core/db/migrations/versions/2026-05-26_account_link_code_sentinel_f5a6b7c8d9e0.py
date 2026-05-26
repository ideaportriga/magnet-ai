# type: ignore
"""Add ``account_link_code.sa_orm_sentinel`` (missed by d3e4f5a6b7c8 / e4f5a6b7c8d9).

The model :class:`AccountLinkCode` inherits ``UUIDAuditBase`` which mixes in
advanced_alchemy's ``SentinelMixin``. That mixin adds a column named
``sa_orm_sentinel`` (used by SQLAlchemy's bulk-insert sentinel logic). Every
ORM SELECT for the model lists the column, so it has to exist in the DB.

Lives in its own revision because the previous backfill (``e4f5a6b7c8d9``)
was already applied to some environments with only ``updated_at`` patched —
Alembic won't re-run a completed revision, so the sentinel column needs a
fresh one.

Idempotent: ``ADD COLUMN IF NOT EXISTS``.

Revision ID: f5a6b7c8d9e0
Revises: e4f5a6b7c8d9
Create Date: 2026-05-26 14:00:00.000000+00:00
"""

from __future__ import annotations

import warnings

from alembic import op

__all__ = ["downgrade", "upgrade", "schema_upgrades", "schema_downgrades"]

revision = "f5a6b7c8d9e0"
down_revision = "e4f5a6b7c8d9"
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
        "ADD COLUMN IF NOT EXISTS sa_orm_sentinel INTEGER NULL"
    )


def schema_downgrades() -> None:
    # Don't drop — keeps downgrade safe even if some other migration starts
    # depending on the column. Re-running upgrade is a no-op (IF NOT EXISTS).
    pass
