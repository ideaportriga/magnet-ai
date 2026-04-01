# type: ignore
"""Create refresh_token, password_reset_token, email_verification_token tables.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-03-29 02:00:00.000000+00:00

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
revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
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
    # 1. refresh_token table
    op.execute("""
        CREATE TABLE IF NOT EXISTS refresh_token (
            id UUID NOT NULL,
            token_hash VARCHAR(64) NOT NULL,
            family_id UUID NOT NULL,
            user_id UUID NOT NULL,
            device_info VARCHAR(512),
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            revoked_at TIMESTAMP WITH TIME ZONE,
            sa_orm_sentinel INTEGER,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
            CONSTRAINT pk_refresh_token PRIMARY KEY (id),
            CONSTRAINT fk_refresh_token_user_id FOREIGN KEY (user_id)
                REFERENCES user_account (id) ON DELETE CASCADE
        )
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ix_refresh_token_token_hash
        ON refresh_token (token_hash)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_refresh_token_family_id
        ON refresh_token (family_id)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_refresh_token_user_id
        ON refresh_token (user_id)
    """)

    # 2. password_reset_token table
    op.execute("""
        CREATE TABLE IF NOT EXISTS password_reset_token (
            id UUID NOT NULL,
            token_hash VARCHAR(64) NOT NULL,
            user_id UUID NOT NULL,
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            used_at TIMESTAMP WITH TIME ZONE,
            ip_address VARCHAR(45),
            sa_orm_sentinel INTEGER,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
            CONSTRAINT pk_password_reset_token PRIMARY KEY (id),
            CONSTRAINT fk_password_reset_token_user_id FOREIGN KEY (user_id)
                REFERENCES user_account (id) ON DELETE CASCADE
        )
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ix_password_reset_token_token_hash
        ON password_reset_token (token_hash)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_password_reset_token_user_id
        ON password_reset_token (user_id)
    """)

    # 3. email_verification_token table
    op.execute("""
        CREATE TABLE IF NOT EXISTS email_verification_token (
            id UUID NOT NULL,
            token_hash VARCHAR(64) NOT NULL,
            email VARCHAR(320) NOT NULL,
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            used_at TIMESTAMP WITH TIME ZONE,
            sa_orm_sentinel INTEGER,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
            CONSTRAINT pk_email_verification_token PRIMARY KEY (id)
        )
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ix_email_verification_token_token_hash
        ON email_verification_token (token_hash)
    """)


def schema_downgrades() -> None:
    # 3. Drop email_verification_token
    op.execute("DROP INDEX IF EXISTS ix_email_verification_token_token_hash")
    op.execute("DROP TABLE IF EXISTS email_verification_token")

    # 2. Drop password_reset_token
    op.execute("DROP INDEX IF EXISTS ix_password_reset_token_user_id")
    op.execute("DROP INDEX IF EXISTS ix_password_reset_token_token_hash")
    op.execute("DROP TABLE IF EXISTS password_reset_token")

    # 1. Drop refresh_token
    op.execute("DROP INDEX IF EXISTS ix_refresh_token_user_id")
    op.execute("DROP INDEX IF EXISTS ix_refresh_token_family_id")
    op.execute("DROP INDEX IF EXISTS ix_refresh_token_token_hash")
    op.execute("DROP TABLE IF EXISTS refresh_token")
