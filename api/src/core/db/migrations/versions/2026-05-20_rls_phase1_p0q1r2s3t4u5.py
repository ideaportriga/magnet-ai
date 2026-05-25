# type: ignore
"""Tenant-isolation RLS — Phase 1: 5 already-tenant-scoped tables.

Phase 1 of the tenant-isolation rollout (see
`docs/tenant-isolation-plan.md`).

These tables already carry `tenant_id` but were missing RLS policies, so
isolation was relying purely on application-level WHERE clauses. This
migration enables row-level security on each one and attaches a
`<table>_tenant_isolation` policy with superuser bypass (same shape as
the policies refreshed in revision o9p0q1r2s3t4).

Tables (5):
    api_keys          — NOT NULL tenant_id, FK RESTRICT (secrets)
    ai_edit_request   — NOT NULL tenant_id, FK CASCADE
    entity_audit_log  — NOT NULL tenant_id, FK CASCADE
    user_account      — NOT NULL tenant_id, FK RESTRICT
    role              — NULLABLE tenant_id; system roles have NULL.
                        Policy has an `OR tenant_id IS NULL` branch so
                        system roles stay readable cross-tenant.

Revision ID: p0q1r2s3t4u5
Revises: o9p0q1r2s3t4
Create Date: 2026-05-20 18:00:00.000000+00:00
"""

from __future__ import annotations

import warnings

from alembic import op

__all__ = ["downgrade", "upgrade", "schema_upgrades", "schema_downgrades"]

revision = "p0q1r2s3t4u5"
down_revision = "o9p0q1r2s3t4"
branch_labels = None
depends_on = None


# Tables that take the standard policy (tenant_id NOT NULL).
_STANDARD_TABLES = [
    "api_keys",
    "ai_edit_request",
    "entity_audit_log",
    "user_account",
]

# Standard policy expression — matches the o9p0q1r2s3t4 migration shape
# so all `*_tenant_isolation` policies have a consistent form.
_STANDARD_USING = """
    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
    OR NULLIF(current_setting('app.is_superuser', true), '') = 'true'
"""

# `role.tenant_id` is nullable: system roles (admin/user/viewer) have
# `tenant_id IS NULL` and must be visible to every tenant. Add an
# OR-branch so the policy still admits them.
_ROLE_USING = """
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
    policy = f"{table}_tenant_isolation"
    op.execute(f"DROP POLICY IF EXISTS {policy} ON {table}")


def schema_upgrades() -> None:
    for table in _STANDARD_TABLES:
        _enable_rls(table)
        _create_policy(table, _STANDARD_USING)

    _enable_rls("role")
    _create_policy("role", _ROLE_USING)


def schema_downgrades() -> None:
    _drop_policy("role")
    _disable_rls("role")

    for table in _STANDARD_TABLES:
        _drop_policy(table)
        _disable_rls(table)
