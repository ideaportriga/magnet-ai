# type: ignore
"""Roll out tenant + record-level access to collections / prompts / ai_apps.

PR 10 #1-3 of `docs/access-control-tenancy-plan-v2_ai-claude.md`.

For each of the three tables we apply the same template proven on `agents`:

  1. Add `tenant_id` (nullable → backfill default → NOT NULL → FK).
  2. Drop the legacy global UNIQUE on `system_name`.
  3. Add partial UNIQUE `(tenant_id, system_name)`.
  4. Add `owner_id`, `department_id`, `visibility` (default 'tenant').
  5. CHECK constraint on `visibility`.
  6. ENABLE + FORCE RLS, CREATE policy `<table>_tenant_isolation`.

Revision ID: b0c1d2e3f4a5
Revises: a9b0c1d2e3f4
Create Date: 2026-05-15 15:00:00.000000+00:00
"""

from __future__ import annotations

import warnings

from alembic import op

__all__ = ["downgrade", "upgrade", "schema_upgrades", "schema_downgrades"]

revision = "b0c1d2e3f4a5"
down_revision = "a9b0c1d2e3f4"
branch_labels = None
depends_on = None


DEFAULT_TENANT_SLUG = "default"
TABLES = ("collections", "prompts", "ai_apps")


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


def _apply_to(table: str) -> None:
    # 1. tenant_id column → backfill → NOT NULL → FK
    op.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS tenant_id UUID")
    op.execute(
        f"""
        UPDATE {table}
        SET tenant_id = (SELECT id FROM tenant WHERE slug = '{DEFAULT_TENANT_SLUG}')
        WHERE tenant_id IS NULL
        """
    )
    op.execute(f"ALTER TABLE {table} ALTER COLUMN tenant_id SET NOT NULL")
    op.execute(
        f"""
        ALTER TABLE {table}
            ADD CONSTRAINT fk_{table}_tenant_id
            FOREIGN KEY (tenant_id) REFERENCES tenant (id) ON DELETE RESTRICT
        """
    )
    op.execute(
        f"CREATE INDEX IF NOT EXISTS ix_{table}_tenant_id ON {table} (tenant_id)"
    )

    # 2. Drop legacy global UNIQUE on system_name (auto-named — find it).
    op.execute(
        f"""
        DO $$
        DECLARE
            cname text;
        BEGIN
            SELECT conname INTO cname
            FROM pg_constraint
            WHERE conrelid = '{table}'::regclass
              AND contype = 'u'
              AND array_length(conkey, 1) = 1
              AND (
                  SELECT attname FROM pg_attribute
                  WHERE attrelid = conrelid AND attnum = conkey[1]
              ) = 'system_name'
            LIMIT 1;
            IF cname IS NOT NULL THEN
                EXECUTE 'ALTER TABLE {table} DROP CONSTRAINT ' || quote_ident(cname);
            END IF;
        END $$;
        """
    )
    op.execute(
        f"""
        DO $$
        DECLARE
            iname text;
        BEGIN
            SELECT i.relname INTO iname
            FROM pg_class i
            JOIN pg_index ix ON ix.indexrelid = i.oid
            JOIN pg_class t ON t.oid = ix.indrelid
            JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
            WHERE t.relname = '{table}'
              AND ix.indisunique
              AND a.attname = 'system_name'
              AND array_length(ix.indkey, 1) = 1
              AND NOT ix.indisprimary
            LIMIT 1;
            IF iname IS NOT NULL THEN
                EXECUTE 'DROP INDEX IF EXISTS ' || quote_ident(iname);
            END IF;
        END $$;
        """
    )

    # 3. Partial unique per tenant.
    op.execute(
        f"""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_{table}_system_name_per_tenant
            ON {table} (tenant_id, system_name)
        """
    )

    # 4. Record-level columns + CHECK.
    op.execute(
        f"""
        ALTER TABLE {table}
            ADD COLUMN IF NOT EXISTS owner_id UUID,
            ADD COLUMN IF NOT EXISTS department_id UUID,
            ADD COLUMN IF NOT EXISTS visibility VARCHAR(20) NOT NULL DEFAULT 'tenant'
        """
    )
    op.execute(
        f"""
        ALTER TABLE {table}
            ADD CONSTRAINT fk_{table}_owner_id
            FOREIGN KEY (owner_id) REFERENCES user_account (id) ON DELETE SET NULL
        """
    )
    op.execute(
        f"""
        ALTER TABLE {table}
            ADD CONSTRAINT fk_{table}_department_id
            FOREIGN KEY (department_id) REFERENCES department (id) ON DELETE SET NULL
        """
    )
    op.execute(
        f"""
        ALTER TABLE {table}
            ADD CONSTRAINT ck_{table}_visibility CHECK (
                visibility IN ('private', 'department', 'tenant')
            )
        """
    )
    op.execute(f"CREATE INDEX IF NOT EXISTS ix_{table}_owner_id ON {table} (owner_id)")
    op.execute(
        f"CREATE INDEX IF NOT EXISTS ix_{table}_department_id ON {table} (department_id)"
    )

    # 5. RLS.
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table}")
    op.execute(
        f"""
        CREATE POLICY {table}_tenant_isolation ON {table}
        FOR ALL
        USING (
            tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
        )
        WITH CHECK (
            tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
        )
        """
    )


def _revert(table: str) -> None:
    op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table}")
    op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
    op.execute(f"DROP INDEX IF EXISTS ix_{table}_department_id")
    op.execute(f"DROP INDEX IF EXISTS ix_{table}_owner_id")
    op.execute(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS ck_{table}_visibility")
    op.execute(
        f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS fk_{table}_department_id"
    )
    op.execute(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS fk_{table}_owner_id")
    op.execute(
        f"""
        ALTER TABLE {table}
            DROP COLUMN IF EXISTS visibility,
            DROP COLUMN IF EXISTS department_id,
            DROP COLUMN IF EXISTS owner_id
        """
    )
    op.execute(f"DROP INDEX IF EXISTS uq_{table}_system_name_per_tenant")
    op.execute(
        f"ALTER TABLE {table} ADD CONSTRAINT {table}_system_name_key UNIQUE (system_name)"
    )
    op.execute(f"DROP INDEX IF EXISTS ix_{table}_tenant_id")
    op.execute(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS fk_{table}_tenant_id")
    op.execute(f"ALTER TABLE {table} DROP COLUMN IF EXISTS tenant_id")


def schema_upgrades() -> None:
    for table in TABLES:
        _apply_to(table)


def schema_downgrades() -> None:
    for table in TABLES:
        _revert(table)
