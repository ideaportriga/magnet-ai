# type: ignore
"""Create oauth_client and oauth_authorization_code tables; extend refresh_token.

Adds the OAuth 2.1 authorization-server data model used when Magnet exposes itself
as an MCP server. Only the storage shape is created here — the OAuth endpoints
themselves are wired up in code (see api/src/mcp_server/).

Two new tables:
- oauth_client: registered OAuth clients (Claude, MCP Inspector, etc.)
- oauth_authorization_code: single-use auth codes (5-min TTL, PKCE-bound)

Two new nullable columns on refresh_token:
- client_id: which OAuth client this refresh-token family belongs to
              (NULL = legacy web-cookie session)
- audience:  RFC 8707 resource URI carried by the access tokens this family
              issues (NULL = web-cookie session)

Revision ID: c0d1e2f3a4b5
Revises: b9c8d7e6f5a4
Create Date: 2026-04-28 00:01:00.000000+00:00

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

revision = "c0d1e2f3a4b5"
down_revision = "b9c8d7e6f5a4"
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
    # 1. oauth_client table
    op.execute("""
        CREATE TABLE IF NOT EXISTS oauth_client (
            id UUID NOT NULL,
            client_id VARCHAR(64) NOT NULL,
            name VARCHAR(255) NOT NULL,
            is_public BOOLEAN NOT NULL DEFAULT TRUE,
            client_secret_encrypted VARCHAR(2048),
            redirect_uris VARCHAR(1024)[] NOT NULL,
            enabled BOOLEAN NOT NULL DEFAULT TRUE,
            created_via VARCHAR(16) NOT NULL DEFAULT 'admin',
            sa_orm_sentinel INTEGER,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
            CONSTRAINT pk_oauth_client PRIMARY KEY (id)
        )
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ix_oauth_client_client_id
        ON oauth_client (client_id)
    """)
    op.execute("""
        COMMENT ON TABLE oauth_client IS
        'OAuth 2.1 clients permitted to use the MCP server'
    """)

    # 2. oauth_authorization_code table
    op.execute("""
        CREATE TABLE IF NOT EXISTS oauth_authorization_code (
            id UUID NOT NULL,
            code_hash VARCHAR(64) NOT NULL,
            client_id VARCHAR(64) NOT NULL,
            user_id UUID NOT NULL,
            redirect_uri VARCHAR(1024) NOT NULL,
            redirect_uri_provided_explicitly BOOLEAN NOT NULL DEFAULT TRUE,
            code_challenge VARCHAR(128) NOT NULL,
            scope VARCHAR(512),
            resource VARCHAR(512),
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            consumed_at TIMESTAMP WITH TIME ZONE,
            sa_orm_sentinel INTEGER,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
            CONSTRAINT pk_oauth_authorization_code PRIMARY KEY (id),
            CONSTRAINT fk_oauth_authorization_code_user_id FOREIGN KEY (user_id)
                REFERENCES user_account (id) ON DELETE CASCADE
        )
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ix_oauth_authorization_code_code_hash
        ON oauth_authorization_code (code_hash)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_oauth_authorization_code_client_id
        ON oauth_authorization_code (client_id)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_oauth_authorization_code_user_id
        ON oauth_authorization_code (user_id)
    """)
    op.execute("""
        COMMENT ON TABLE oauth_authorization_code IS
        'Single-use OAuth authorization codes (5-min TTL)'
    """)

    # 3. refresh_token: add client_id + audience nullable columns
    op.execute("""
        ALTER TABLE refresh_token
        ADD COLUMN IF NOT EXISTS client_id VARCHAR(64) DEFAULT NULL
    """)
    op.execute("""
        ALTER TABLE refresh_token
        ADD COLUMN IF NOT EXISTS audience VARCHAR(512) DEFAULT NULL
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_refresh_token_client_id
        ON refresh_token (client_id)
        WHERE client_id IS NOT NULL
    """)
    op.execute("""
        COMMENT ON COLUMN refresh_token.client_id IS
        'OAuth client_id when this token was minted for an MCP/OAuth flow (NULL = web-cookie session)'
    """)
    op.execute("""
        COMMENT ON COLUMN refresh_token.audience IS
        'Audience (aud claim) carried by access tokens this family issues. NULL = web cookie.'
    """)


def schema_downgrades() -> None:
    # 4. Drop seeded row implicitly via DROP TABLE below.

    # 3. refresh_token: drop added columns + index
    op.execute("DROP INDEX IF EXISTS ix_refresh_token_client_id")
    op.execute("ALTER TABLE refresh_token DROP COLUMN IF EXISTS audience")
    op.execute("ALTER TABLE refresh_token DROP COLUMN IF EXISTS client_id")

    # 2. Drop oauth_authorization_code
    op.execute("DROP INDEX IF EXISTS ix_oauth_authorization_code_user_id")
    op.execute("DROP INDEX IF EXISTS ix_oauth_authorization_code_client_id")
    op.execute("DROP INDEX IF EXISTS ix_oauth_authorization_code_code_hash")
    op.execute("DROP TABLE IF EXISTS oauth_authorization_code")

    # 1. Drop oauth_client
    op.execute("DROP INDEX IF EXISTS ix_oauth_client_client_id")
    op.execute("DROP TABLE IF EXISTS oauth_client")
