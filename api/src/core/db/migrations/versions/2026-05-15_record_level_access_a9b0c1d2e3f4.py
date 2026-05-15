# type: ignore
"""Record-level access pilot: departments, grants, agents.{owner_id,department_id,visibility}.

PR 8 of `docs/access-control-tenancy-plan-v2_ai-claude.md`.

  - department + user_department tables
  - resource_access_grant table
  - agents gets owner_id (NULL allowed for legacy rows), department_id, visibility
  - default visibility is 'tenant' so existing rows stay visible inside tenant

Revision ID: a9b0c1d2e3f4
Revises: f8a9b0c1d2e3
Create Date: 2026-05-15 14:00:00.000000+00:00
"""

from __future__ import annotations

import warnings

from alembic import op

__all__ = ["downgrade", "upgrade", "schema_upgrades", "schema_downgrades"]

revision = "a9b0c1d2e3f4"
down_revision = "f8a9b0c1d2e3"
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
    # ── department ────────────────────────────────────────────────────────
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS department (
            id UUID NOT NULL,
            tenant_id UUID NOT NULL,
            slug VARCHAR(100) NOT NULL,
            name VARCHAR(255) NOT NULL,
            parent_id UUID,
            sa_orm_sentinel INTEGER,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
            CONSTRAINT pk_department PRIMARY KEY (id),
            CONSTRAINT fk_department_tenant_id FOREIGN KEY (tenant_id)
                REFERENCES tenant (id) ON DELETE CASCADE,
            CONSTRAINT fk_department_parent_id FOREIGN KEY (parent_id)
                REFERENCES department (id) ON DELETE SET NULL
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_department_tenant_id ON department (tenant_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_department_parent_id ON department (parent_id)"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_department_slug_per_tenant "
        "ON department (tenant_id, slug)"
    )

    # ── user_department ───────────────────────────────────────────────────
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS user_department (
            id UUID NOT NULL,
            tenant_id UUID NOT NULL,
            user_id UUID NOT NULL,
            department_id UUID NOT NULL,
            is_lead BOOLEAN NOT NULL DEFAULT FALSE,
            sa_orm_sentinel INTEGER,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
            CONSTRAINT pk_user_department PRIMARY KEY (id),
            CONSTRAINT fk_user_department_tenant_id FOREIGN KEY (tenant_id)
                REFERENCES tenant (id) ON DELETE CASCADE,
            CONSTRAINT fk_user_department_user_id FOREIGN KEY (user_id)
                REFERENCES user_account (id) ON DELETE CASCADE,
            CONSTRAINT fk_user_department_department_id FOREIGN KEY (department_id)
                REFERENCES department (id) ON DELETE CASCADE,
            CONSTRAINT uq_user_department UNIQUE (user_id, department_id)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_user_department_tenant_id ON user_department (tenant_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_user_department_user_id ON user_department (user_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_user_department_department_id "
        "ON user_department (department_id)"
    )

    # ── resource_access_grant ─────────────────────────────────────────────
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS resource_access_grant (
            id UUID NOT NULL,
            tenant_id UUID NOT NULL,
            resource_type VARCHAR(100) NOT NULL,
            resource_id UUID NOT NULL,
            principal_type VARCHAR(20) NOT NULL,
            principal_id UUID NOT NULL,
            access_level VARCHAR(20) NOT NULL,
            granted_by_id UUID,
            sa_orm_sentinel INTEGER,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
            CONSTRAINT pk_resource_access_grant PRIMARY KEY (id),
            CONSTRAINT fk_resource_access_grant_tenant_id FOREIGN KEY (tenant_id)
                REFERENCES tenant (id) ON DELETE CASCADE,
            CONSTRAINT fk_resource_access_grant_granted_by_id FOREIGN KEY (granted_by_id)
                REFERENCES user_account (id) ON DELETE SET NULL,
            CONSTRAINT uq_resource_access_grant UNIQUE (
                tenant_id, resource_type, resource_id, principal_type, principal_id
            )
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_resource_access_grant_tenant_id "
        "ON resource_access_grant (tenant_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_resource_access_grant_lookup "
        "ON resource_access_grant (tenant_id, resource_type, resource_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_resource_access_grant_principal "
        "ON resource_access_grant (tenant_id, principal_type, principal_id)"
    )

    # ── agents record-level columns ───────────────────────────────────────
    op.execute(
        """
        ALTER TABLE agents
            ADD COLUMN IF NOT EXISTS owner_id UUID,
            ADD COLUMN IF NOT EXISTS department_id UUID,
            ADD COLUMN IF NOT EXISTS visibility VARCHAR(20) NOT NULL DEFAULT 'tenant'
        """
    )
    op.execute(
        """
        ALTER TABLE agents
            ADD CONSTRAINT fk_agents_owner_id
            FOREIGN KEY (owner_id) REFERENCES user_account (id) ON DELETE SET NULL
        """
    )
    op.execute(
        """
        ALTER TABLE agents
            ADD CONSTRAINT fk_agents_department_id
            FOREIGN KEY (department_id) REFERENCES department (id) ON DELETE SET NULL
        """
    )
    op.execute(
        """
        ALTER TABLE agents
            ADD CONSTRAINT ck_agents_visibility CHECK (
                visibility IN ('private', 'department', 'tenant')
            )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_agents_owner_id ON agents (owner_id)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_agents_department_id ON agents (department_id)"
    )


def schema_downgrades() -> None:
    op.execute("DROP INDEX IF EXISTS ix_agents_department_id")
    op.execute("DROP INDEX IF EXISTS ix_agents_owner_id")
    op.execute("ALTER TABLE agents DROP CONSTRAINT IF EXISTS ck_agents_visibility")
    op.execute("ALTER TABLE agents DROP CONSTRAINT IF EXISTS fk_agents_department_id")
    op.execute("ALTER TABLE agents DROP CONSTRAINT IF EXISTS fk_agents_owner_id")
    op.execute(
        """
        ALTER TABLE agents
            DROP COLUMN IF EXISTS visibility,
            DROP COLUMN IF EXISTS department_id,
            DROP COLUMN IF EXISTS owner_id
        """
    )

    op.execute("DROP INDEX IF EXISTS ix_resource_access_grant_principal")
    op.execute("DROP INDEX IF EXISTS ix_resource_access_grant_lookup")
    op.execute("DROP INDEX IF EXISTS ix_resource_access_grant_tenant_id")
    op.execute("DROP TABLE IF EXISTS resource_access_grant")

    op.execute("DROP INDEX IF EXISTS ix_user_department_department_id")
    op.execute("DROP INDEX IF EXISTS ix_user_department_user_id")
    op.execute("DROP INDEX IF EXISTS ix_user_department_tenant_id")
    op.execute("DROP TABLE IF EXISTS user_department")

    op.execute("DROP INDEX IF EXISTS uq_department_slug_per_tenant")
    op.execute("DROP INDEX IF EXISTS ix_department_parent_id")
    op.execute("DROP INDEX IF EXISTS ix_department_tenant_id")
    op.execute("DROP TABLE IF EXISTS department")
