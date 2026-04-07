# type: ignore
"""Add scopes column to api_keys table.

Supports fine-grained permission control for API keys.
NULL scopes = legacy key with default 'user' role access.

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-04-07 00:01:00.000000+00:00

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

revision = "a7b8c9d0e1f2"
down_revision = "f6a7b8c9d0e1"
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
    # Add scopes column (JSONB, nullable).
    # NULL = legacy key (backward compatible, gets 'user' role).
    # Empty array [] = no scopes (most restrictive).
    # ["read:projects", "write:datasets"] = explicit scopes.
    op.execute("""
        ALTER TABLE api_keys
        ADD COLUMN IF NOT EXISTS scopes JSONB DEFAULT NULL
    """)

    # Add comment for documentation
    op.execute("""
        COMMENT ON COLUMN api_keys.scopes IS
        'Permission scopes (e.g. ["read:projects"]). NULL = legacy key with default user role.'
    """)


def schema_downgrades() -> None:
    op.execute("ALTER TABLE api_keys DROP COLUMN IF EXISTS scopes")
