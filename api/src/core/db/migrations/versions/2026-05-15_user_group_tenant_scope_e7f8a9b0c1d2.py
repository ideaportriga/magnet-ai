# type: ignore
"""Tenant-scope user_group: add tenant_id and partial unique indexes.

PR 6 of `docs/access-control-tenancy-plan-v2_ai-claude.md`.

  - Add `user_group.tenant_id` (nullable → backfill default → NOT NULL → FK)
  - Drop global UNIQUE on (slug) and (name)
  - Create partial unique indexes per (tenant_id, slug) and (tenant_id, name)

Revision ID: e7f8a9b0c1d2
Revises: d6e7f8a9b0c1
Create Date: 2026-05-15 12:00:00.000000+00:00
"""

from __future__ import annotations

import warnings

from alembic import op

__all__ = ["downgrade", "upgrade", "schema_upgrades", "schema_downgrades"]

revision = "e7f8a9b0c1d2"
down_revision = "d6e7f8a9b0c1"
branch_labels = None
depends_on = None


DEFAULT_TENANT_SLUG = "default"


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
    # 1. Add nullable column.
    op.execute(
        """
        ALTER TABLE user_group
            ADD COLUMN IF NOT EXISTS tenant_id UUID
        """
    )

    # 2. Backfill to default tenant.
    op.execute(
        f"""
        UPDATE user_group
        SET tenant_id = (SELECT id FROM tenant WHERE slug = '{DEFAULT_TENANT_SLUG}')
        WHERE tenant_id IS NULL
        """
    )

    # 3. NOT NULL + FK.
    op.execute(
        """
        ALTER TABLE user_group
            ALTER COLUMN tenant_id SET NOT NULL
        """
    )
    op.execute(
        """
        ALTER TABLE user_group
            ADD CONSTRAINT fk_user_group_tenant_id
            FOREIGN KEY (tenant_id) REFERENCES tenant (id) ON DELETE CASCADE
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_user_group_tenant_id ON user_group (tenant_id)"
    )

    # 4. Replace global UNIQUE on slug/name with per-tenant partial unique.
    op.execute("ALTER TABLE user_group DROP CONSTRAINT IF EXISTS uq_user_group_slug")
    op.execute("ALTER TABLE user_group DROP CONSTRAINT IF EXISTS uq_user_group_name")

    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_user_group_slug_per_tenant
            ON user_group (tenant_id, slug)
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_user_group_name_per_tenant
            ON user_group (tenant_id, name)
        """
    )


def schema_downgrades() -> None:
    op.execute("DROP INDEX IF EXISTS uq_user_group_name_per_tenant")
    op.execute("DROP INDEX IF EXISTS uq_user_group_slug_per_tenant")
    op.execute("ALTER TABLE user_group ADD CONSTRAINT uq_user_group_name UNIQUE (name)")
    op.execute("ALTER TABLE user_group ADD CONSTRAINT uq_user_group_slug UNIQUE (slug)")
    op.execute("DROP INDEX IF EXISTS ix_user_group_tenant_id")
    op.execute(
        "ALTER TABLE user_group DROP CONSTRAINT IF EXISTS fk_user_group_tenant_id"
    )
    op.execute("ALTER TABLE user_group DROP COLUMN IF EXISTS tenant_id")
