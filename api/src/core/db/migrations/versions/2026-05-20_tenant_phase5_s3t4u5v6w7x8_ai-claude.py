# type: ignore
"""Tenant-isolation Phase 5 — denormalize tenant_id from parent.

Tables whose tenant is unambiguous via a parent FK get their own
`tenant_id` column (denormalized for cheap filtering and clean RLS).

Standard tenant_id (NOT NULL, CASCADE):
  knowledge_graph_metadata_discoveries  ← knowledge_graphs.tenant_id
  knowledge_graph_metadata_extractions  ← knowledge_graphs.tenant_id
  knowledge_graph_sources               ← knowledge_graphs.tenant_id
  oauth_authorization_code              ← user_account.tenant_id
  password_reset_token                  ← user_account.tenant_id
  refresh_token                         ← user_account.tenant_id
  user_account_oauth                    ← user_account.tenant_id
  user_role                             ← user_account.tenant_id

Nullable tenant_id (IS NULL for system rows, see role policy):
  role_permission                       ← role.tenant_id (NULL for system roles)

Excluded by design:
  email_verification_token              — pre-auth, user does not exist yet (Q-5).

Revision ID: s3t4u5v6w7x8
Revises: r2s3t4u5v6w7
Create Date: 2026-05-20 20:00:00.000000+00:00
"""

from __future__ import annotations

import warnings

from alembic import op

__all__ = ["downgrade", "upgrade", "schema_upgrades", "schema_downgrades"]

revision = "s3t4u5v6w7x8"
down_revision = "r2s3t4u5v6w7"
branch_labels = None
depends_on = None


_STANDARD_USING = """
    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
    OR NULLIF(current_setting('app.is_superuser', true), '') = 'true'
"""

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


def _denormalize(
    table: str,
    backfill_sql: str,
    *,
    using_expr: str = _STANDARD_USING,
    nullable: bool = False,
    on_delete: str = "CASCADE",
) -> None:
    op.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS tenant_id UUID")
    op.execute(backfill_sql)
    if not nullable:
        # Drop rows we couldn't attribute (orphan FK).
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
        USING ({using_expr})
        WITH CHECK ({using_expr})
        """
    )


def schema_upgrades() -> None:
    # ── knowledge_graph children (via graph_id → knowledge_graphs) ──────
    for child in (
        "knowledge_graph_metadata_discoveries",
        "knowledge_graph_metadata_extractions",
        "knowledge_graph_sources",
    ):
        _denormalize(
            child,
            f"""
            UPDATE {child} c
            SET tenant_id = kg.tenant_id
            FROM knowledge_graphs kg
            WHERE c.tenant_id IS NULL
              AND kg.id = c.graph_id
            """,
        )

    # ── token tables (via user_id → user_account) ──────────────────────
    for tbl in (
        "oauth_authorization_code",
        "password_reset_token",
        "refresh_token",
        "user_account_oauth",
    ):
        _denormalize(
            tbl,
            f"""
            UPDATE {tbl} t
            SET tenant_id = u.tenant_id
            FROM user_account u
            WHERE t.tenant_id IS NULL
              AND u.id = t.user_id
            """,
        )

    # ── user_role (via user_id → user_account) ─────────────────────────
    _denormalize(
        "user_role",
        """
        UPDATE user_role ur
        SET tenant_id = u.tenant_id
        FROM user_account u
        WHERE ur.tenant_id IS NULL
          AND u.id = ur.user_id
        """,
    )

    # ── role_permission (via role_id → role.tenant_id, NULL for system) ─
    _denormalize(
        "role_permission",
        """
        UPDATE role_permission rp
        SET tenant_id = r.tenant_id
        FROM role r
        WHERE rp.tenant_id IS NULL
          AND r.id = rp.role_id
        """,
        using_expr=_NULLABLE_USING,
        nullable=True,
    )


def schema_downgrades() -> None:
    for table in (
        "role_permission",
        "user_role",
        "user_account_oauth",
        "refresh_token",
        "password_reset_token",
        "oauth_authorization_code",
        "knowledge_graph_sources",
        "knowledge_graph_metadata_extractions",
        "knowledge_graph_metadata_discoveries",
    ):
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
        op.execute(f"DROP INDEX IF EXISTS ix_{table}_tenant_id")
        op.execute(
            f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS fk_{table}_tenant_id"
        )
        op.execute(f"ALTER TABLE {table} DROP COLUMN IF EXISTS tenant_id")
