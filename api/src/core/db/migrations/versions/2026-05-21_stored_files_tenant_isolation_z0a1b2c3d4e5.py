# type: ignore
"""Add tenant_id + tenant_isolation RLS to ``stored_files``.

Until now `stored_files` was a global table with no tenant column, so
``GET /files/`` and ``GET /files/{id}/download`` leaked cross-tenant
attachments. Bring it in line with the rest of the schema:

  1. ADD COLUMN ``tenant_id`` UUID (nullable initially).
  2. Backfill from the parent entity wherever possible:
       - ``entity_type='ks_source'`` → ``knowledge_graph_sources.tenant_id``
     Remaining rows fall back to the ``default`` tenant.
  3. ALTER → NOT NULL + FK to ``tenant(id)`` ON DELETE RESTRICT + index.
  4. ENABLE + FORCE RLS, CREATE POLICY ``stored_files_tenant_isolation``
     with the same template used by the other tenant-isolated tables
     (matches ``app.tenant_id`` GUC, or ``app.is_superuser='true'``).

Once this lands, the ``before_flush`` listener in ``core.db.rls_context``
auto-populates ``tenant_id`` from the request context for every new
``StoredFile`` — no caller-side changes needed.

Revision ID: z0a1b2c3d4e5
Revises: u5v6w7x8y9z0
Create Date: 2026-05-21 00:45:00.000000+00:00
"""

from __future__ import annotations

import warnings

from alembic import op

__all__ = ["downgrade", "upgrade", "schema_upgrades", "schema_downgrades"]

revision = "z0a1b2c3d4e5"
down_revision = "u5v6w7x8y9z0"
branch_labels = None
depends_on = None


_TABLE = "stored_files"
_DEFAULT_TENANT_SLUG = "default"


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
    # 1. tenant_id column (nullable while we backfill).
    op.execute(f"ALTER TABLE {_TABLE} ADD COLUMN IF NOT EXISTS tenant_id UUID")

    # 2a. Backfill from the parent knowledge_graph_source.
    op.execute(
        f"""
        UPDATE {_TABLE} sf
        SET tenant_id = kgs.tenant_id
        FROM knowledge_graph_sources kgs
        WHERE sf.tenant_id IS NULL
          AND sf.entity_type = 'ks_source'
          AND sf.entity_id = kgs.id
        """
    )

    # 2b. Anything still null → default tenant (temp uploads, orphans).
    op.execute(
        f"""
        UPDATE {_TABLE}
        SET tenant_id = (SELECT id FROM tenant WHERE slug = '{_DEFAULT_TENANT_SLUG}')
        WHERE tenant_id IS NULL
        """
    )

    # 3. Constraints + index.
    op.execute(f"ALTER TABLE {_TABLE} ALTER COLUMN tenant_id SET NOT NULL")
    op.execute(
        f"""
        ALTER TABLE {_TABLE}
            ADD CONSTRAINT fk_{_TABLE}_tenant_id
            FOREIGN KEY (tenant_id) REFERENCES tenant (id) ON DELETE RESTRICT
        """
    )
    op.execute(
        f"CREATE INDEX IF NOT EXISTS ix_{_TABLE}_tenant_id ON {_TABLE} (tenant_id)"
    )

    # 4. RLS.
    op.execute(f"ALTER TABLE {_TABLE} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {_TABLE} FORCE ROW LEVEL SECURITY")
    op.execute(f"DROP POLICY IF EXISTS {_TABLE}_tenant_isolation ON {_TABLE}")
    op.execute(
        f"""
        CREATE POLICY {_TABLE}_tenant_isolation ON {_TABLE}
        FOR ALL
        USING (
            tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
            OR NULLIF(current_setting('app.is_superuser', true), '') = 'true'
        )
        WITH CHECK (
            tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
            OR NULLIF(current_setting('app.is_superuser', true), '') = 'true'
        )
        """
    )


def schema_downgrades() -> None:
    op.execute(f"DROP POLICY IF EXISTS {_TABLE}_tenant_isolation ON {_TABLE}")
    op.execute(f"ALTER TABLE {_TABLE} NO FORCE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {_TABLE} DISABLE ROW LEVEL SECURITY")
    op.execute(f"DROP INDEX IF EXISTS ix_{_TABLE}_tenant_id")
    op.execute(f"ALTER TABLE {_TABLE} DROP CONSTRAINT IF EXISTS fk_{_TABLE}_tenant_id")
    op.execute(f"ALTER TABLE {_TABLE} DROP COLUMN IF EXISTS tenant_id")
