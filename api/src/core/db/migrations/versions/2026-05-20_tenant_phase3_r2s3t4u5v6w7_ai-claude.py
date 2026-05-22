# type: ignore
"""Tenant-isolation Phase 3 — children of tenant-scoped parents.

Adds `tenant_id` + RLS to tables whose tenant is derivable from a
tenant-scoped parent row.

  deep_research_runs              — via config_system_name → deep_research_configs
  evaluations                     — via test_sets[0] → evaluation_sets.system_name
  api_tools                       — via api_provider → api_servers.system_name
  note_taker_integration_attempt  — via job_id → note_taker_jobs.id
  note_taker_pending_confirmation — via job_id → note_taker_jobs.id

All NOT NULL after backfill. Orphan rows (parent missing) are deleted —
they have no tenant attribution and would block the NOT NULL constraint.

Revision ID: r2s3t4u5v6w7
Revises: q1r2s3t4u5v6
Create Date: 2026-05-20 19:30:00.000000+00:00
"""

from __future__ import annotations

import warnings

from alembic import op

__all__ = ["downgrade", "upgrade", "schema_upgrades", "schema_downgrades"]

revision = "r2s3t4u5v6w7"
down_revision = "q1r2s3t4u5v6"
branch_labels = None
depends_on = None


_STANDARD_USING = """
    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
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


def _add_tenant_id(
    table: str,
    backfill_sql: str,
    *,
    on_delete: str = "CASCADE",
) -> None:
    """Standard "add nullable, backfill, drop orphans, NOT NULL + FK + RLS" routine."""
    op.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS tenant_id UUID")
    op.execute(backfill_sql)
    # Drop any rows we couldn't attribute.
    op.execute(f"DELETE FROM {table} WHERE tenant_id IS NULL")
    op.execute(f"ALTER TABLE {table} ALTER COLUMN tenant_id SET NOT NULL")
    # Idempotent: drop the FK if a previous (partial) run created it.
    # autocommit_block commits each statement, so a crash mid-migration
    # leaves the constraint behind while alembic_version is unchanged.
    op.execute(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS fk_{table}_tenant_id")
    op.execute(
        f"""
        ALTER TABLE {table}
            ADD CONSTRAINT fk_{table}_tenant_id
            FOREIGN KEY (tenant_id) REFERENCES tenant (id) ON DELETE {on_delete}
        """
    )
    op.execute(
        f"CREATE INDEX IF NOT EXISTS ix_{table}_tenant_id ON {table} (tenant_id)"
    )
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table}")
    op.execute(
        f"""
        CREATE POLICY {table}_tenant_isolation ON {table}
        FOR ALL
        USING ({_STANDARD_USING})
        WITH CHECK ({_STANDARD_USING})
        """
    )


def schema_upgrades() -> None:
    # ── deep_research_runs ──────────────────────────────────────────────
    _add_tenant_id(
        "deep_research_runs",
        """
        UPDATE deep_research_runs r
        SET tenant_id = c.tenant_id
        FROM deep_research_configs c
        WHERE r.tenant_id IS NULL
          AND r.config_system_name IS NOT NULL
          AND c.system_name = r.config_system_name
        """,
    )

    # ── evaluations ─────────────────────────────────────────────────────
    # test_sets is a JSONB list of system_names; take the first to look up
    # the tenant. Cross-tenant test sets are blocked by RLS, so all entries
    # of any well-formed list share a tenant.
    _add_tenant_id(
        "evaluations",
        """
        UPDATE evaluations e
        SET tenant_id = es.tenant_id
        FROM evaluation_sets es
        WHERE e.tenant_id IS NULL
          AND jsonb_typeof(e.test_sets) = 'array'
          AND jsonb_array_length(e.test_sets) > 0
          AND es.system_name = (e.test_sets ->> 0)
        """,
    )

    # ── api_tools ───────────────────────────────────────────────────────
    _add_tenant_id(
        "api_tools",
        """
        UPDATE api_tools t
        SET tenant_id = s.tenant_id
        FROM api_servers s
        WHERE t.tenant_id IS NULL
          AND t.api_provider IS NOT NULL
          AND s.system_name = t.api_provider
        """,
    )

    # ── note_taker_integration_attempt ─────────────────────────────────
    # job_id is a text column; note_taker_jobs.id is UUID — cast.
    _add_tenant_id(
        "note_taker_integration_attempt",
        """
        UPDATE note_taker_integration_attempt a
        SET tenant_id = j.tenant_id
        FROM note_taker_jobs j
        WHERE a.tenant_id IS NULL
          AND a.job_id IS NOT NULL
          AND a.job_id <> ''
          AND j.id::text = a.job_id
        """,
    )

    # ── note_taker_pending_confirmation ────────────────────────────────
    _add_tenant_id(
        "note_taker_pending_confirmation",
        """
        UPDATE note_taker_pending_confirmation pc
        SET tenant_id = j.tenant_id
        FROM note_taker_jobs j
        WHERE pc.tenant_id IS NULL
          AND pc.job_id IS NOT NULL
          AND pc.job_id <> ''
          AND j.id::text = pc.job_id
        """,
    )


def schema_downgrades() -> None:
    for table in (
        "note_taker_pending_confirmation",
        "note_taker_integration_attempt",
        "api_tools",
        "evaluations",
        "deep_research_runs",
    ):
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
        op.execute(f"DROP INDEX IF EXISTS ix_{table}_tenant_id")
        op.execute(
            f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS fk_{table}_tenant_id"
        )
        op.execute(f"ALTER TABLE {table} DROP COLUMN IF EXISTS tenant_id")
