# type: ignore
"""Tenant base: tenant table + tenant_id on user_account, api_keys, role.

Implements PR 4 of `docs/access-control-tenancy-plan-v2_ai-claude.md`:
  - create `tenant` table
  - seed the `default` tenant
  - add `user_account.tenant_id` (nullable → backfill → NOT NULL)
  - add `api_keys.tenant_id` (nullable → backfill → NOT NULL)
  - add `role.tenant_id` (nullable; NULL for system roles)
  - drop global UNIQUE(role.slug)/UNIQUE(role.name)
  - add partial unique indexes per (tenant_id, slug/name)
  - add CHECK invariant: system role ⇔ tenant_id IS NULL

No record-level changes yet (PR 7/8).

Revision ID: c5d6e7f8a9b0
Revises: b4c5d6e7f8a9
Create Date: 2026-05-15 10:00:00.000000+00:00
"""

from __future__ import annotations

import warnings

from alembic import op

__all__ = ["downgrade", "upgrade", "schema_upgrades", "schema_downgrades"]

revision = "c5d6e7f8a9b0"
down_revision = "b4c5d6e7f8a9"
branch_labels = None
depends_on = None


DEFAULT_TENANT_SLUG = "default"
DEFAULT_TENANT_NAME = "Default"


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
    # 1. tenant table -------------------------------------------------------
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS tenant (
            id UUID NOT NULL,
            slug VARCHAR(100) NOT NULL,
            name VARCHAR(255) NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            sa_orm_sentinel INTEGER,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
            CONSTRAINT pk_tenant PRIMARY KEY (id),
            CONSTRAINT uq_tenant_slug UNIQUE (slug)
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_tenant_slug ON tenant (slug)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tenant_is_active ON tenant (is_active)")

    # Seed default tenant. Idempotent.
    op.execute(
        f"""
        INSERT INTO tenant (id, slug, name, is_active, created_at, updated_at)
        VALUES (
            gen_random_uuid(),
            '{DEFAULT_TENANT_SLUG}',
            '{DEFAULT_TENANT_NAME}',
            TRUE,
            NOW(),
            NOW()
        )
        ON CONFLICT (slug) DO NOTHING
        """
    )

    # 2. user_account.tenant_id --------------------------------------------
    op.execute(
        """
        ALTER TABLE user_account
            ADD COLUMN IF NOT EXISTS tenant_id UUID
        """
    )
    # Backfill all existing rows to the default tenant.
    op.execute(
        f"""
        UPDATE user_account
        SET tenant_id = (SELECT id FROM tenant WHERE slug = '{DEFAULT_TENANT_SLUG}')
        WHERE tenant_id IS NULL
        """
    )
    op.execute(
        """
        ALTER TABLE user_account
            ALTER COLUMN tenant_id SET NOT NULL
        """
    )
    op.execute(
        """
        ALTER TABLE user_account
            ADD CONSTRAINT fk_user_account_tenant_id
            FOREIGN KEY (tenant_id) REFERENCES tenant (id) ON DELETE RESTRICT
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_user_account_tenant_id "
        "ON user_account (tenant_id)"
    )

    # 3. api_keys.tenant_id ------------------------------------------------
    op.execute(
        """
        ALTER TABLE api_keys
            ADD COLUMN IF NOT EXISTS tenant_id UUID
        """
    )
    op.execute(
        f"""
        UPDATE api_keys
        SET tenant_id = COALESCE(
            (SELECT u.tenant_id FROM user_account u WHERE u.id = api_keys.user_id),
            (SELECT id FROM tenant WHERE slug = '{DEFAULT_TENANT_SLUG}')
        )
        WHERE tenant_id IS NULL
        """
    )
    op.execute(
        """
        ALTER TABLE api_keys
            ALTER COLUMN tenant_id SET NOT NULL
        """
    )
    op.execute(
        """
        ALTER TABLE api_keys
            ADD CONSTRAINT fk_api_keys_tenant_id
            FOREIGN KEY (tenant_id) REFERENCES tenant (id) ON DELETE RESTRICT
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_api_keys_tenant_id ON api_keys (tenant_id)"
    )

    # 4. role.tenant_id + partial unique + CHECK ---------------------------
    op.execute(
        """
        ALTER TABLE role
            ADD COLUMN IF NOT EXISTS tenant_id UUID
        """
    )
    op.execute(
        """
        ALTER TABLE role
            ADD CONSTRAINT fk_role_tenant_id
            FOREIGN KEY (tenant_id) REFERENCES tenant (id) ON DELETE CASCADE
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_role_tenant_id ON role (tenant_id)")

    # Existing rows are all system roles (admin/user/viewer, is_system=TRUE
    # via PR 2). System roles keep tenant_id = NULL by design.
    # Custom tenant roles (is_system=FALSE) will have tenant_id set on insert
    # (admin UI lands in PR 5).
    op.execute(
        """
        ALTER TABLE role
            ADD CONSTRAINT ck_role_system_invariant CHECK (
                (is_system = TRUE AND tenant_id IS NULL) OR
                (is_system = FALSE AND tenant_id IS NOT NULL)
            )
        """
    )

    # Drop global UNIQUE on slug/name so two tenants can have a custom role
    # named 'reviewer'. System roles stay globally unique via partial index.
    op.execute("ALTER TABLE role DROP CONSTRAINT IF EXISTS uq_role_slug")
    op.execute("ALTER TABLE role DROP CONSTRAINT IF EXISTS uq_role_name")

    # System roles: tenant_id IS NULL; slug and name unique among system roles.
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_role_slug_system
            ON role (slug) WHERE tenant_id IS NULL
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_role_name_system
            ON role (name) WHERE tenant_id IS NULL
        """
    )
    # Custom roles: unique within their tenant.
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_role_slug_per_tenant
            ON role (tenant_id, slug) WHERE tenant_id IS NOT NULL
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_role_name_per_tenant
            ON role (tenant_id, name) WHERE tenant_id IS NOT NULL
        """
    )


def schema_downgrades() -> None:
    # role
    op.execute("DROP INDEX IF EXISTS uq_role_name_per_tenant")
    op.execute("DROP INDEX IF EXISTS uq_role_slug_per_tenant")
    op.execute("DROP INDEX IF EXISTS uq_role_name_system")
    op.execute("DROP INDEX IF EXISTS uq_role_slug_system")
    op.execute("ALTER TABLE role ADD CONSTRAINT uq_role_name UNIQUE (name)")
    op.execute("ALTER TABLE role ADD CONSTRAINT uq_role_slug UNIQUE (slug)")
    op.execute("ALTER TABLE role DROP CONSTRAINT IF EXISTS ck_role_system_invariant")
    op.execute("DROP INDEX IF EXISTS ix_role_tenant_id")
    op.execute("ALTER TABLE role DROP CONSTRAINT IF EXISTS fk_role_tenant_id")
    op.execute("ALTER TABLE role DROP COLUMN IF EXISTS tenant_id")

    # api_keys
    op.execute("DROP INDEX IF EXISTS ix_api_keys_tenant_id")
    op.execute("ALTER TABLE api_keys DROP CONSTRAINT IF EXISTS fk_api_keys_tenant_id")
    op.execute("ALTER TABLE api_keys DROP COLUMN IF EXISTS tenant_id")

    # user_account
    op.execute("DROP INDEX IF EXISTS ix_user_account_tenant_id")
    op.execute(
        "ALTER TABLE user_account DROP CONSTRAINT IF EXISTS fk_user_account_tenant_id"
    )
    op.execute("ALTER TABLE user_account DROP COLUMN IF EXISTS tenant_id")

    # tenant
    op.execute("DROP INDEX IF EXISTS ix_tenant_is_active")
    op.execute("DROP INDEX IF EXISTS ix_tenant_slug")
    op.execute("DROP TABLE IF EXISTS tenant")
