# type: ignore
"""Create user_account and user_account_oauth tables, add user_id FK to api_keys.

Revision ID: a1b2c3d4e5f7
Revises: f7e8d9c0b1a2
Create Date: 2026-03-29 00:00:00.000000+00:00

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


# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f7"
down_revision = "f7e8d9c0b1a2"
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
    # 1. user_account table
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_account (
            id UUID NOT NULL,
            email VARCHAR(320) NOT NULL,
            name VARCHAR(255),
            avatar_url VARCHAR(2048),
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
            is_verified BOOLEAN NOT NULL DEFAULT FALSE,
            last_login_at TIMESTAMP WITH TIME ZONE,
            hashed_password VARCHAR(255),
            sa_orm_sentinel INTEGER,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
            CONSTRAINT pk_user_account PRIMARY KEY (id)
        )
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ix_user_account_email
        ON user_account (email)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_user_account_is_active
        ON user_account (is_active)
    """)

    # 2. user_account_oauth table
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_account_oauth (
            id UUID NOT NULL,
            user_id UUID NOT NULL,
            oauth_name VARCHAR(100) NOT NULL,
            account_id VARCHAR(320) NOT NULL,
            account_email VARCHAR(320),
            last_login_at TIMESTAMP WITH TIME ZONE,
            sa_orm_sentinel INTEGER,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
            CONSTRAINT pk_user_account_oauth PRIMARY KEY (id),
            CONSTRAINT fk_user_account_oauth_user_id FOREIGN KEY (user_id)
                REFERENCES user_account (id) ON DELETE CASCADE
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_user_account_oauth_user_id
        ON user_account_oauth (user_id)
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_oauth_provider_account
        ON user_account_oauth (oauth_name, account_id)
    """)

    # 3. Add optional user_id FK to api_keys
    op.execute("""
        ALTER TABLE api_keys
        ADD COLUMN IF NOT EXISTS user_id UUID
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_name = 'fk_api_keys_user_id'
            ) THEN
                ALTER TABLE api_keys
                ADD CONSTRAINT fk_api_keys_user_id
                FOREIGN KEY (user_id) REFERENCES user_account (id) ON DELETE SET NULL;
            END IF;
        END $$
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_api_keys_user_id
        ON api_keys (user_id)
    """)


def schema_downgrades() -> None:
    # 3. Remove user_id from api_keys
    op.execute("ALTER TABLE api_keys DROP CONSTRAINT IF EXISTS fk_api_keys_user_id")
    op.execute("DROP INDEX IF EXISTS ix_api_keys_user_id")
    op.execute("ALTER TABLE api_keys DROP COLUMN IF EXISTS user_id")

    # 2. Drop user_account_oauth
    op.execute("DROP INDEX IF EXISTS uq_oauth_provider_account")
    op.execute("DROP INDEX IF EXISTS ix_user_account_oauth_user_id")
    op.execute("DROP TABLE IF EXISTS user_account_oauth")

    # 1. Drop user_account
    op.execute("DROP INDEX IF EXISTS ix_user_account_is_active")
    op.execute("DROP INDEX IF EXISTS ix_user_account_email")
    op.execute("DROP TABLE IF EXISTS user_account")
