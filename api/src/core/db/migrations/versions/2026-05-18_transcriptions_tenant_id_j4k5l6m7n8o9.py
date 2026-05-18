# type: ignore
"""Add tenant_id + RLS policy to transcriptions.

Closes the HIGH security gap from `docs/note_taker/NOTETAKER_AS_IS.md` §
"Уязвимости текущей архитектуры" #2: `transcriptions` had no tenant
boundary, so an admin in tenant A could fetch any transcription —
including those from tenants B/C — via `GET /api/admin/recordings/{job_id}/transcription`.

The column is NULLABLE in this revision because both pipeline entry
points (HTTP routes + taskiq workers) need code changes to populate it
before NOT NULL is safe. RLS still hides rows where `tenant_id IS NULL`
(no current_setting match), so the gap is closed even during the
transition window: legacy / unattributed rows become admin-only via the
JIT bypass that role-based access already covers.

A follow-up migration will flip the column to NOT NULL once metrics show
zero NULL inserts for a week.

See NOTE_TAKER_REVISION_PLAN.md §3.4 P3-b.

Revision ID: j4k5l6m7n8o9
Revises: i3j4k5l6m7n8
Create Date: 2026-05-18 18:00:00.000000+00:00
"""

from __future__ import annotations

import warnings

from alembic import op

__all__ = ["downgrade", "upgrade", "schema_upgrades", "schema_downgrades"]

revision = "j4k5l6m7n8o9"
down_revision = "i3j4k5l6m7n8"
branch_labels = None
depends_on = None


TABLE = "transcriptions"
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
    op.execute(f"ALTER TABLE {TABLE} ADD COLUMN IF NOT EXISTS tenant_id UUID")

    # Backfill: every existing row predates tenancy → assign to default
    # tenant. Operators with multiple tenants must reassign manually
    # post-migration if cross-tenant transcriptions ended up co-mingled
    # in the legacy table (unlikely — STT was single-tenant pre-rollout).
    op.execute(
        f"""
        UPDATE {TABLE}
        SET tenant_id = (SELECT id FROM tenant WHERE slug = '{DEFAULT_TENANT_SLUG}')
        WHERE tenant_id IS NULL
        """
    )

    op.execute(
        f"""
        ALTER TABLE {TABLE}
            ADD CONSTRAINT fk_{TABLE}_tenant_id
            FOREIGN KEY (tenant_id) REFERENCES tenant (id) ON DELETE RESTRICT
        """
    )
    op.execute(
        f"CREATE INDEX IF NOT EXISTS ix_{TABLE}_tenant_id ON {TABLE} (tenant_id)"
    )

    op.execute(f"ALTER TABLE {TABLE} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {TABLE} FORCE ROW LEVEL SECURITY")
    op.execute(f"DROP POLICY IF EXISTS {TABLE}_tenant_isolation ON {TABLE}")
    op.execute(
        f"""
        CREATE POLICY {TABLE}_tenant_isolation ON {TABLE}
        FOR ALL
        USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
        WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
        """
    )


def schema_downgrades() -> None:
    op.execute(f"DROP POLICY IF EXISTS {TABLE}_tenant_isolation ON {TABLE}")
    op.execute(f"ALTER TABLE {TABLE} NO FORCE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {TABLE} DISABLE ROW LEVEL SECURITY")
    op.execute(f"DROP INDEX IF EXISTS ix_{TABLE}_tenant_id")
    op.execute(f"ALTER TABLE {TABLE} DROP CONSTRAINT IF EXISTS fk_{TABLE}_tenant_id")
    op.execute(f"ALTER TABLE {TABLE} DROP COLUMN IF EXISTS tenant_id")
