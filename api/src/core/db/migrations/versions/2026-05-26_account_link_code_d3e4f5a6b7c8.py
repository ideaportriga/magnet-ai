# type: ignore
"""Add ``account_link_code`` — generic pairing codes for binding any external
identity to an internal ``user_account``.

A user on an external surface (Teams bot, Slack bot, Discord, CLI device-flow,
…) requests a code via that surface, then pastes it into the admin UI while
authenticated. The backend resolves the code → ``(provider, subject_id)`` and
inserts a ``user_account_oauth`` row.

The table is pre-auth (no tenant scoping) by design: the code is created
before the consuming user is known. Pairs are short-lived (10-min TTL) and
indexed by code (the unguessable lookup key). One active code per
``(provider, subject_id, channel_id)`` is enforced via partial unique index.

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-05-26 09:00:00.000000+00:00
"""

from __future__ import annotations

import warnings

from alembic import op

__all__ = ["downgrade", "upgrade", "schema_upgrades", "schema_downgrades"]

revision = "d3e4f5a6b7c8"
down_revision = "c2d3e4f5a6b7"
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
        """
        CREATE TABLE IF NOT EXISTS account_link_code (
            id UUID PRIMARY KEY,
            code VARCHAR(32) NOT NULL,

            -- External identity being claimed by the code.
            provider VARCHAR(64) NOT NULL,
            subject_id TEXT NOT NULL,

            -- Optional source-channel context (e.g. Teams bot id, Slack
            -- workspace id). Used both for disambiguating concurrent /link
            -- sessions and for picking the right post-consume hook.
            channel_kind VARCHAR(32) NULL,
            channel_id TEXT NULL,

            -- Snapshot rendered by the confirm UI so the user can verify
            -- which external identity they're about to bind.
            display_name TEXT,
            email TEXT,
            extra JSONB,

            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            expires_at TIMESTAMPTZ NOT NULL,
            consumed_at TIMESTAMPTZ NULL,
            consumed_by_user_id UUID NULL REFERENCES user_account (id) ON DELETE SET NULL,

            CONSTRAINT uq_account_link_code_code UNIQUE (code)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_account_link_code_code "
        "ON account_link_code (code) WHERE consumed_at IS NULL"
    )
    # One active code per (provider, subject_id, channel_id). COALESCE keeps
    # the partial index well-defined for rows without a channel_id.
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_account_link_code_active "
        "ON account_link_code (provider, subject_id, COALESCE(channel_id, '')) "
        "WHERE consumed_at IS NULL"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_account_link_code_expires_at "
        "ON account_link_code (expires_at)"
    )


def schema_downgrades() -> None:
    op.execute("DROP INDEX IF EXISTS ix_account_link_code_expires_at")
    op.execute("DROP INDEX IF EXISTS uq_account_link_code_active")
    op.execute("DROP INDEX IF EXISTS ix_account_link_code_code")
    op.execute("DROP TABLE IF EXISTS account_link_code")
