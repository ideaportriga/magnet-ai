# type: ignore
"""Add MFA fields to user_account table.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-03-29 04:00:00.000000+00:00

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

revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
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
        ALTER TABLE user_account
        ADD COLUMN IF NOT EXISTS is_two_factor_enabled BOOLEAN NOT NULL DEFAULT FALSE
    """)
    op.execute("""
        ALTER TABLE user_account
        ADD COLUMN IF NOT EXISTS totp_secret VARCHAR(255)
    """)
    op.execute("""
        ALTER TABLE user_account
        ADD COLUMN IF NOT EXISTS backup_codes JSONB
    """)
    op.execute("""
        ALTER TABLE user_account
        ADD COLUMN IF NOT EXISTS two_factor_confirmed_at TIMESTAMP WITH TIME ZONE
    """)


def schema_downgrades() -> None:
    op.execute("ALTER TABLE user_account DROP COLUMN IF EXISTS two_factor_confirmed_at")
    op.execute("ALTER TABLE user_account DROP COLUMN IF EXISTS backup_codes")
    op.execute("ALTER TABLE user_account DROP COLUMN IF EXISTS totp_secret")
    op.execute("ALTER TABLE user_account DROP COLUMN IF EXISTS is_two_factor_enabled")
