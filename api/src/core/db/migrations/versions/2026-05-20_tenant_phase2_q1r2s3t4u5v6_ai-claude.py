# type: ignore
"""Tenant-isolation Phase 2 — observability + agent conversations.

Adds `tenant_id` + RLS to three tables that previously had no tenant
scoping:

  traces              — nullable tenant_id; backfilled from user_account
                        via user_id. Orphan traces (no user_id or user
                        deleted) keep NULL.  Policy: IS NULL OR match.
  metrics             — nullable tenant_id; backfilled from traces via
                        trace_id (after traces is filled).  Policy:
                        IS NULL OR match.
  agent_conversations — NOT NULL tenant_id; backfilled by joining
                        agents on system_name = agent. Conversations
                        with no resolvable agent are deleted (cannot
                        be tenant-attributed).

See `docs/tenant-isolation-plan_ai-claude.md` for the full plan.

Revision ID: q1r2s3t4u5v6
Revises: p0q1r2s3t4u5
Create Date: 2026-05-20 19:00:00.000000+00:00
"""

from __future__ import annotations

import warnings

from alembic import op

__all__ = ["downgrade", "upgrade", "schema_upgrades", "schema_downgrades"]

revision = "q1r2s3t4u5v6"
down_revision = "p0q1r2s3t4u5"
branch_labels = None
depends_on = None


_STANDARD_USING = """
    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
    OR NULLIF(current_setting('app.is_superuser', true), '') = 'true'
"""

# Used for tables with nullable tenant_id (system rows have NULL).
_NULLABLE_USING = """
    tenant_id IS NULL
    OR tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
    OR NULLIF(current_setting('app.is_superuser', true), '') = 'true'
"""


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


def _enable_rls(table: str) -> None:
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")


def _disable_rls(table: str) -> None:
    op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")


def _create_policy(table: str, using_expr: str) -> None:
    policy = f"{table}_tenant_isolation"
    op.execute(f"DROP POLICY IF EXISTS {policy} ON {table}")
    op.execute(
        f"""
        CREATE POLICY {policy} ON {table}
        FOR ALL
        USING ({using_expr})
        WITH CHECK ({using_expr})
        """
    )


def _drop_policy(table: str) -> None:
    op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table}")


def schema_upgrades() -> None:
    # ── traces (nullable tenant_id) ─────────────────────────────────────
    op.execute("ALTER TABLE traces ADD COLUMN IF NOT EXISTS tenant_id UUID")
    # Backfill from user_account by user_id (traces.user_id is a string,
    # user_account.id is UUID — cast safely with NULLIF + ::uuid).
    op.execute(
        """
        UPDATE traces t
        SET tenant_id = u.tenant_id
        FROM user_account u
        WHERE t.tenant_id IS NULL
          AND t.user_id IS NOT NULL
          AND t.user_id <> ''
          AND u.id::text = t.user_id
        """
    )
    # Idempotent: drop the FK if a previous (partial) run created it.
    # autocommit_block commits each statement, so a crash mid-migration
    # leaves the constraint behind while alembic_version is unchanged.
    op.execute("ALTER TABLE traces DROP CONSTRAINT IF EXISTS fk_traces_tenant_id")
    op.execute(
        """
        ALTER TABLE traces
            ADD CONSTRAINT fk_traces_tenant_id
            FOREIGN KEY (tenant_id) REFERENCES tenant (id) ON DELETE CASCADE
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_traces_tenant_id ON traces (tenant_id)")
    _enable_rls("traces")
    _create_policy("traces", _NULLABLE_USING)

    # ── metrics (nullable tenant_id) ────────────────────────────────────
    op.execute("ALTER TABLE metrics ADD COLUMN IF NOT EXISTS tenant_id UUID")
    # Backfill from traces via trace_id.
    op.execute(
        """
        UPDATE metrics m
        SET tenant_id = t.tenant_id
        FROM traces t
        WHERE m.tenant_id IS NULL
          AND m.trace_id IS NOT NULL
          AND t.id = m.trace_id
        """
    )
    op.execute("ALTER TABLE metrics DROP CONSTRAINT IF EXISTS fk_metrics_tenant_id")
    op.execute(
        """
        ALTER TABLE metrics
            ADD CONSTRAINT fk_metrics_tenant_id
            FOREIGN KEY (tenant_id) REFERENCES tenant (id) ON DELETE CASCADE
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_metrics_tenant_id ON metrics (tenant_id)")
    _enable_rls("metrics")
    _create_policy("metrics", _NULLABLE_USING)

    # ── agent_conversations (NOT NULL tenant_id) ────────────────────────
    op.execute(
        "ALTER TABLE agent_conversations ADD COLUMN IF NOT EXISTS tenant_id UUID"
    )
    # Backfill via agents.system_name = agent_conversations.agent. agents
    # already carries tenant_id (since 2026-05-15_agents_rls_f8a9b0c1d2e3),
    # so the join is unambiguous (system_name is unique per tenant).
    op.execute(
        """
        UPDATE agent_conversations ac
        SET tenant_id = a.tenant_id
        FROM agents a
        WHERE ac.tenant_id IS NULL
          AND ac.agent IS NOT NULL
          AND a.system_name = ac.agent
        """
    )
    # Conversations whose agent cannot be resolved (orphan / typo agent
    # name) fall back to the default tenant — preserves legacy data and
    # closes the autocommit-gap race with old replicas still inserting.
    op.execute(
        """
        UPDATE agent_conversations
        SET tenant_id = (SELECT id FROM tenant WHERE slug = 'default')
        WHERE tenant_id IS NULL
        """
    )
    op.execute("ALTER TABLE agent_conversations ALTER COLUMN tenant_id SET NOT NULL")
    op.execute(
        "ALTER TABLE agent_conversations "
        "DROP CONSTRAINT IF EXISTS fk_agent_conversations_tenant_id"
    )
    op.execute(
        """
        ALTER TABLE agent_conversations
            ADD CONSTRAINT fk_agent_conversations_tenant_id
            FOREIGN KEY (tenant_id) REFERENCES tenant (id) ON DELETE CASCADE
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_agent_conversations_tenant_id "
        "ON agent_conversations (tenant_id)"
    )
    _enable_rls("agent_conversations")
    _create_policy("agent_conversations", _STANDARD_USING)


def schema_downgrades() -> None:
    for table in ("agent_conversations", "metrics", "traces"):
        _drop_policy(table)
        _disable_rls(table)
        op.execute(f"DROP INDEX IF EXISTS ix_{table}_tenant_id")
        op.execute(
            f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS fk_{table}_tenant_id"
        )
        op.execute(f"ALTER TABLE {table} DROP COLUMN IF EXISTS tenant_id")
