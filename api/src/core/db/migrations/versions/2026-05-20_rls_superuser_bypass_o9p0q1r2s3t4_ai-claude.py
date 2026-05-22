# type: ignore
"""Add application-level superuser bypass to all tenant_isolation RLS policies.

Until now tenant isolation worked only by chance: the app was connecting as
the Postgres ``postgres`` role (SUPERUSER + BYPASSRLS), so all RLS policies
were no-ops. Fixing that means switching the runtime to a non-superuser
role — but then ``User.is_superuser`` accounts (cross-tenant god mode at
the application layer) would also lose visibility, because the policy only
matches when ``tenant_id`` equals the GUC.

Fix: propagate the application's superuser flag into a third GUC
``app.is_superuser`` (alongside ``app.tenant_id`` and ``app.user_id``,
emitted by the SQLAlchemy ``after_begin`` listener in
``core.db.rls_context``), and extend every ``*_tenant_isolation`` policy
with an OR-clause that opens row visibility when that GUC is ``'true'``.

Empty/unset GUC continues to fail closed (NULLIF returns NULL).

Policies updated (20):
    access_audit_log, agents, ai_apps, api_servers, collections,
    deep_research_configs, department, evaluation_sets, knowledge_graphs,
    mcp_servers, note_taker_jobs, note_taker_settings, prompts,
    rag_tools, resource_access_grant, retrieval_tools, transcriptions,
    user_department, user_group, user_group_member

`knowledge_graph_metadata_discoveries`, `knowledge_graph_metadata_extractions`
and `knowledge_graph_sources` are intentionally excluded — they have no
`tenant_id` column and inherit scoping from their parent `knowledge_graphs`
row, so a per-row RLS policy on them would be meaningless.

Revision ID: o9p0q1r2s3t4
Revises: n8o9p0q1r2s3
Create Date: 2026-05-20 10:00:00.000000+00:00
"""

from __future__ import annotations

import warnings

from alembic import op

__all__ = ["downgrade", "upgrade", "schema_upgrades", "schema_downgrades"]

revision = "o9p0q1r2s3t4"
down_revision = "n8o9p0q1r2s3"
branch_labels = None
depends_on = None


# Tables that currently have a `<table>_tenant_isolation` policy.
_TABLES = [
    "access_audit_log",
    "agents",
    "ai_apps",
    "api_servers",
    "collections",
    "deep_research_configs",
    "department",
    "evaluation_sets",
    "knowledge_graphs",
    "mcp_servers",
    "note_taker_jobs",
    "note_taker_settings",
    "prompts",
    "rag_tools",
    "resource_access_grant",
    "retrieval_tools",
    "transcriptions",
    "user_department",
    "user_group",
    "user_group_member",
]


_NEW_USING = """
    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
    OR NULLIF(current_setting('app.is_superuser', true), '') = 'true'
"""


_OLD_USING = """
    tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
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


def _recreate_policy(table: str, using_expr: str) -> None:
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


def schema_upgrades() -> None:
    for table in _TABLES:
        _recreate_policy(table, _NEW_USING)


def schema_downgrades() -> None:
    for table in _TABLES:
        _recreate_policy(table, _OLD_USING)
