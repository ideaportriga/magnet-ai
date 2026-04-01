# type: ignore
"""Create RBAC tables (role, user_role, user_group, user_group_member) and seed default roles.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f7
Create Date: 2026-03-29 01:00:00.000000+00:00

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
revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f7"
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
    # 1. role table
    op.execute("""
        CREATE TABLE IF NOT EXISTS role (
            id UUID NOT NULL,
            name VARCHAR(100) NOT NULL,
            slug VARCHAR(100) NOT NULL,
            description TEXT,
            sa_orm_sentinel INTEGER,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
            CONSTRAINT pk_role PRIMARY KEY (id),
            CONSTRAINT uq_role_name UNIQUE (name),
            CONSTRAINT uq_role_slug UNIQUE (slug)
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_role_slug ON role (slug)
    """)

    # 2. user_role table
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_role (
            id UUID NOT NULL,
            user_id UUID NOT NULL,
            role_id UUID NOT NULL,
            assigned_at TIMESTAMP WITH TIME ZONE NOT NULL,
            sa_orm_sentinel INTEGER,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
            CONSTRAINT pk_user_role PRIMARY KEY (id),
            CONSTRAINT fk_user_role_user_id FOREIGN KEY (user_id)
                REFERENCES user_account (id) ON DELETE CASCADE,
            CONSTRAINT fk_user_role_role_id FOREIGN KEY (role_id)
                REFERENCES role (id) ON DELETE CASCADE,
            CONSTRAINT uq_user_role UNIQUE (user_id, role_id)
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_user_role_user_id ON user_role (user_id)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_user_role_role_id ON user_role (role_id)
    """)

    # 3. user_group table (groups)
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_group (
            id UUID NOT NULL,
            name VARCHAR(255) NOT NULL,
            slug VARCHAR(255) NOT NULL,
            description TEXT,
            sa_orm_sentinel INTEGER,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
            CONSTRAINT pk_user_group PRIMARY KEY (id),
            CONSTRAINT uq_user_group_name UNIQUE (name),
            CONSTRAINT uq_user_group_slug UNIQUE (slug)
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_user_group_slug ON user_group (slug)
    """)

    # 4. user_group_member table (many-to-many)
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_group_member (
            id UUID NOT NULL,
            user_id UUID NOT NULL,
            group_id UUID NOT NULL,
            role_in_group VARCHAR(50) NOT NULL DEFAULT 'member',
            assigned_at TIMESTAMP WITH TIME ZONE NOT NULL,
            sa_orm_sentinel INTEGER,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
            CONSTRAINT pk_user_group_member PRIMARY KEY (id),
            CONSTRAINT fk_user_group_member_user_id FOREIGN KEY (user_id)
                REFERENCES user_account (id) ON DELETE CASCADE,
            CONSTRAINT fk_user_group_member_group_id FOREIGN KEY (group_id)
                REFERENCES user_group (id) ON DELETE CASCADE,
            CONSTRAINT uq_user_group_member UNIQUE (user_id, group_id)
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_user_group_member_user_id ON user_group_member (user_id)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_user_group_member_group_id ON user_group_member (group_id)
    """)

    # 5. Seed default roles
    op.execute("""
        INSERT INTO role (id, name, slug, description, created_at, updated_at)
        VALUES (
            gen_random_uuid(),
            'Admin',
            'admin',
            'Full administrative access',
            NOW(),
            NOW()
        )
        ON CONFLICT (slug) DO NOTHING
    """)
    op.execute("""
        INSERT INTO role (id, name, slug, description, created_at, updated_at)
        VALUES (
            gen_random_uuid(),
            'User',
            'user',
            'Default user role with basic access',
            NOW(),
            NOW()
        )
        ON CONFLICT (slug) DO NOTHING
    """)


def schema_downgrades() -> None:
    # 4. Drop user_group_member
    op.execute("DROP INDEX IF EXISTS ix_user_group_member_group_id")
    op.execute("DROP INDEX IF EXISTS ix_user_group_member_user_id")
    op.execute("DROP TABLE IF EXISTS user_group_member")

    # 3. Drop user_group
    op.execute("DROP INDEX IF EXISTS ix_user_group_slug")
    op.execute("DROP TABLE IF EXISTS user_group")

    # 2. Drop user_role
    op.execute("DROP INDEX IF EXISTS ix_user_role_role_id")
    op.execute("DROP INDEX IF EXISTS ix_user_role_user_id")
    op.execute("DROP TABLE IF EXISTS user_role")

    # 1. Drop role
    op.execute("DROP INDEX IF EXISTS ix_role_slug")
    op.execute("DROP TABLE IF EXISTS role")
