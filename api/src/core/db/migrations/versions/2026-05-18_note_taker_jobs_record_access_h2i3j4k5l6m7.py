# type: ignore
"""Add tenant + record-level access columns to note_taker_jobs.

Continuation of the PR 10 rollout for the Note Taker domain:
`note_taker_settings` got tenant/owner/visibility in revision e3f4a5b6c7d8;
`note_taker_jobs` (the admin preview runs) still lacked them, which blocked
record-level RBAC at the jobs controller (see NOTE_TAKER_REVISION_PLAN.md
§3.4 P3-a — the Phase 1 controller falls back to a local user_id check
because the model has no `owner_id`/`tenant_id`).

Behaviours added:
* `tenant_id` NOT NULL, FK → tenant.id, RLS policy on the table.
* `owner_id` NULLABLE, FK → user_account.id (set from `force_create_fields`
  on new rows; legacy rows are backfilled where `user_id` parses to a
  user_account row).
* `department_id`, `visibility` columns to match the rest of the rollout
  cohort. Default visibility is `'private'` (preview jobs are personal
  runs — admins still see all rows by virtue of the system admin role).

Revision ID: h2i3j4k5l6m7
Revises: g1h2i3j4k5l6
Create Date: 2026-05-18 17:00:00.000000+00:00
"""

from __future__ import annotations

import warnings

from alembic import op

__all__ = ["downgrade", "upgrade", "schema_upgrades", "schema_downgrades"]

revision = "h2i3j4k5l6m7"
down_revision = "g1h2i3j4k5l6"
branch_labels = None
depends_on = None


DEFAULT_TENANT_SLUG = "default"
TABLE = "note_taker_jobs"


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
    op.execute(
        f"""
        UPDATE {TABLE}
        SET tenant_id = (SELECT id FROM tenant WHERE slug = '{DEFAULT_TENANT_SLUG}')
        WHERE tenant_id IS NULL
        """
    )
    op.execute(f"ALTER TABLE {TABLE} ALTER COLUMN tenant_id SET NOT NULL")
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

    op.execute(
        f"""
        ALTER TABLE {TABLE}
            ADD COLUMN IF NOT EXISTS owner_id UUID,
            ADD COLUMN IF NOT EXISTS department_id UUID,
            ADD COLUMN IF NOT EXISTS visibility VARCHAR(20) NOT NULL DEFAULT 'private'
        """
    )

    # Backfill `owner_id` from the existing `user_id` Text column where it
    # parses as a UUID and points at an actual user_account row. Anything
    # that doesn't match (api-key principals, free-form strings, deleted
    # users) stays NULL — those rows become admin-only via the controller
    # ownership check, which is the safer default.
    op.execute(
        f"""
        UPDATE {TABLE} j
        SET owner_id = u.id
        FROM user_account u
        WHERE j.owner_id IS NULL
          AND j.user_id IS NOT NULL
          AND j.user_id ~ '^[0-9a-fA-F-]{{36}}$'
          AND u.id = j.user_id::uuid
        """
    )

    op.execute(
        f"""
        ALTER TABLE {TABLE}
            ADD CONSTRAINT fk_{TABLE}_owner_id
            FOREIGN KEY (owner_id) REFERENCES user_account (id) ON DELETE SET NULL
        """
    )
    op.execute(
        f"""
        ALTER TABLE {TABLE}
            ADD CONSTRAINT fk_{TABLE}_department_id
            FOREIGN KEY (department_id) REFERENCES department (id) ON DELETE SET NULL
        """
    )
    op.execute(
        f"""
        ALTER TABLE {TABLE}
            ADD CONSTRAINT ck_{TABLE}_visibility CHECK (
                visibility IN ('private', 'department', 'tenant')
            )
        """
    )
    op.execute(f"CREATE INDEX IF NOT EXISTS ix_{TABLE}_owner_id ON {TABLE} (owner_id)")
    op.execute(
        f"CREATE INDEX IF NOT EXISTS ix_{TABLE}_department_id ON {TABLE} (department_id)"
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
    op.execute(f"DROP INDEX IF EXISTS ix_{TABLE}_department_id")
    op.execute(f"DROP INDEX IF EXISTS ix_{TABLE}_owner_id")
    op.execute(f"ALTER TABLE {TABLE} DROP CONSTRAINT IF EXISTS ck_{TABLE}_visibility")
    op.execute(
        f"ALTER TABLE {TABLE} DROP CONSTRAINT IF EXISTS fk_{TABLE}_department_id"
    )
    op.execute(f"ALTER TABLE {TABLE} DROP CONSTRAINT IF EXISTS fk_{TABLE}_owner_id")
    op.execute(
        f"""
        ALTER TABLE {TABLE}
            DROP COLUMN IF EXISTS visibility,
            DROP COLUMN IF EXISTS department_id,
            DROP COLUMN IF EXISTS owner_id
        """
    )
    op.execute(f"DROP INDEX IF EXISTS ix_{TABLE}_tenant_id")
    op.execute(f"ALTER TABLE {TABLE} DROP CONSTRAINT IF EXISTS fk_{TABLE}_tenant_id")
    op.execute(f"ALTER TABLE {TABLE} DROP COLUMN IF EXISTS tenant_id")
