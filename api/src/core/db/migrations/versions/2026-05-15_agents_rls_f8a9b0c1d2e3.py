# type: ignore
"""Tenant isolation for `agents`: tenant_id + partial unique + RLS.

PR 7 of `docs/access-control-tenancy-plan-v2_ai-claude.md`.

This is the architectural turning point of the plan — the first tenant-
scoped resource table protected by Postgres Row-Level Security. After this
migration, every query against `agents` must run inside a transaction with
`SET LOCAL app.tenant_id = '<uuid>'` (emitted by the SQLAlchemy session
event installed in `core.db.rls_context`).

Migration steps:

  1. `agents.tenant_id` — nullable → backfill default → NOT NULL → FK.
  2. Drop the legacy global UNIQUE on `system_name`.
  3. Create partial UNIQUE `(tenant_id, system_name)` so two tenants can
     each have a `default-agent`.
  4. ENABLE + FORCE ROW LEVEL SECURITY (FORCE applies to table owner too,
     so superuser app connections don't accidentally bypass).
  5. CREATE POLICY `agents_tenant_isolation` with USING + WITH CHECK
     comparing `tenant_id` to `current_setting('app.tenant_id')`.

After RLS is on, a connection with no `app.tenant_id` GUC sees zero rows
and cannot INSERT — fail closed.

Revision ID: f8a9b0c1d2e3
Revises: e7f8a9b0c1d2
Create Date: 2026-05-15 13:00:00.000000+00:00
"""

from __future__ import annotations

import warnings

from alembic import op

__all__ = ["downgrade", "upgrade", "schema_upgrades", "schema_downgrades"]

revision = "f8a9b0c1d2e3"
down_revision = "e7f8a9b0c1d2"
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
    # 1. tenant_id column.
    op.execute(
        """
        ALTER TABLE agents
            ADD COLUMN IF NOT EXISTS tenant_id UUID
        """
    )
    op.execute(
        f"""
        UPDATE agents
        SET tenant_id = (SELECT id FROM tenant WHERE slug = '{DEFAULT_TENANT_SLUG}')
        WHERE tenant_id IS NULL
        """
    )
    op.execute(
        """
        ALTER TABLE agents
            ALTER COLUMN tenant_id SET NOT NULL
        """
    )
    op.execute(
        """
        ALTER TABLE agents
            ADD CONSTRAINT fk_agents_tenant_id
            FOREIGN KEY (tenant_id) REFERENCES tenant (id) ON DELETE RESTRICT
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_agents_tenant_id ON agents (tenant_id)")

    # 2. Drop legacy global UNIQUE on system_name. The constraint name is
    #    auto-generated (Postgres default `agents_system_name_key` or the
    #    SQLAlchemy convention `uq_agents_system_name`). Find and drop
    #    whichever single-column unique constraint applies — safer than
    #    hard-coding a name.
    op.execute(
        """
        DO $$
        DECLARE
            cname text;
        BEGIN
            SELECT conname INTO cname
            FROM pg_constraint
            WHERE conrelid = 'agents'::regclass
              AND contype = 'u'
              AND array_length(conkey, 1) = 1
              AND (
                  SELECT attname FROM pg_attribute
                  WHERE attrelid = conrelid AND attnum = conkey[1]
              ) = 'system_name'
            LIMIT 1;
            IF cname IS NOT NULL THEN
                EXECUTE 'ALTER TABLE agents DROP CONSTRAINT ' || quote_ident(cname);
            END IF;
        END $$;
        """
    )
    # Same idea for any standalone unique index on system_name.
    op.execute(
        """
        DO $$
        DECLARE
            iname text;
        BEGIN
            SELECT i.relname INTO iname
            FROM pg_class i
            JOIN pg_index ix ON ix.indexrelid = i.oid
            JOIN pg_class t ON t.oid = ix.indrelid
            JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
            WHERE t.relname = 'agents'
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
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_agents_system_name_per_tenant
            ON agents (tenant_id, system_name)
        """
    )

    # 4. Enable + FORCE RLS.
    op.execute("ALTER TABLE agents ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE agents FORCE ROW LEVEL SECURITY")

    # 5. Policy. Empty / unset GUC fails closed (no rows visible, no inserts
    #    accepted) because `tenant_id` is a UUID and comparing to NULL is
    #    NULL → false.
    op.execute("DROP POLICY IF EXISTS agents_tenant_isolation ON agents")
    op.execute(
        """
        CREATE POLICY agents_tenant_isolation ON agents
        FOR ALL
        USING (
            tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
        )
        WITH CHECK (
            tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
        )
        """
    )


def schema_downgrades() -> None:
    op.execute("DROP POLICY IF EXISTS agents_tenant_isolation ON agents")
    op.execute("ALTER TABLE agents NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE agents DISABLE ROW LEVEL SECURITY")

    op.execute("DROP INDEX IF EXISTS uq_agents_system_name_per_tenant")
    op.execute(
        "ALTER TABLE agents ADD CONSTRAINT agents_system_name_key UNIQUE (system_name)"
    )

    op.execute("DROP INDEX IF EXISTS ix_agents_tenant_id")
    op.execute("ALTER TABLE agents DROP CONSTRAINT IF EXISTS fk_agents_tenant_id")
    op.execute("ALTER TABLE agents DROP COLUMN IF EXISTS tenant_id")
