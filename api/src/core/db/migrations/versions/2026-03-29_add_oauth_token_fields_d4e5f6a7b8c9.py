# type: ignore
"""Add OAuth token fields to user_account_oauth table.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-03-29 03:00:00.000000+00:00

"""

from __future__ import annotations

import warnings

from alembic import op

__all__ = [
    "downgrade",
    "upgrade",
    "schema_upgrades",
    "schema_downgrades",
]

revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
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
    op.execute("""
        ALTER TABLE user_account_oauth
        ADD COLUMN IF NOT EXISTS access_token TEXT
    """)
    op.execute("""
        ALTER TABLE user_account_oauth
        ADD COLUMN IF NOT EXISTS refresh_token TEXT
    """)
    op.execute("""
        ALTER TABLE user_account_oauth
        ADD COLUMN IF NOT EXISTS expires_at BIGINT
    """)


def schema_downgrades() -> None:
    op.execute("ALTER TABLE user_account_oauth DROP COLUMN IF EXISTS expires_at")
    op.execute("ALTER TABLE user_account_oauth DROP COLUMN IF EXISTS refresh_token")
    op.execute("ALTER TABLE user_account_oauth DROP COLUMN IF EXISTS access_token")
