# type: ignore
"""RBAC tenant integrity and support-table RLS hardening.

Revision ID: g1h2i3j4k5l6
Revises: f4a5b6c7d8e9
Create Date: 2026-05-16 00:00:00.000000+00:00
"""

from __future__ import annotations

import warnings

from alembic import op

__all__ = ["downgrade", "upgrade", "schema_upgrades", "schema_downgrades"]

revision = "g1h2i3j4k5l6"
down_revision = "f4a5b6c7d8e9"
branch_labels = None
depends_on = None

TENANT_RLS_TABLES = (
    "user_group",
    "user_group_member",
    "department",
    "user_department",
    "resource_access_grant",
    "access_audit_log",
)


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
    # Support fast composite tenant-safe FKs from resource owner/department fields.
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_user_account_id_tenant "
        "ON user_account (id, tenant_id)"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_department_id_tenant "
        "ON department (id, tenant_id)"
    )

    _add_resource_integrity("agents")
    for table in (
        "collections",
        "prompts",
        "ai_apps",
        "rag_tools",
        "retrieval_tools",
        "api_servers",
        "mcp_servers",
        "evaluation_sets",
        "deep_research_configs",
        "note_taker_settings",
        "knowledge_graphs",
    ):
        _add_resource_integrity(table)

    _add_user_group_member_tenant_id()
    _create_group_member_tenant_trigger()
    _create_user_role_tenant_trigger()

    for table in TENANT_RLS_TABLES:
        _enable_tenant_rls(table)

    _add_kg_child_rls("knowledge_graph_sources")
    _add_kg_child_rls("knowledge_graph_metadata_discoveries")
    _add_kg_child_rls("knowledge_graph_metadata_extractions")


def schema_downgrades() -> None:
    _drop_kg_child_rls("knowledge_graph_metadata_extractions")
    _drop_kg_child_rls("knowledge_graph_metadata_discoveries")
    _drop_kg_child_rls("knowledge_graph_sources")

    for table in reversed(TENANT_RLS_TABLES):
        _disable_tenant_rls(table)

    op.execute("DROP TRIGGER IF EXISTS trg_user_role_tenant_integrity ON user_role")
    op.execute("DROP FUNCTION IF EXISTS enforce_user_role_tenant_integrity()")
    op.execute(
        "DROP TRIGGER IF EXISTS trg_user_group_member_tenant_integrity "
        "ON user_group_member"
    )
    op.execute("DROP FUNCTION IF EXISTS enforce_user_group_member_tenant_integrity()")
    _drop_user_group_member_tenant_id()

    for table in (
        "knowledge_graphs",
        "note_taker_settings",
        "deep_research_configs",
        "evaluation_sets",
        "mcp_servers",
        "api_servers",
        "retrieval_tools",
        "rag_tools",
        "ai_apps",
        "prompts",
        "collections",
        "agents",
    ):
        _drop_resource_integrity(table)

    op.execute("DROP INDEX IF EXISTS uq_department_id_tenant")
    op.execute("DROP INDEX IF EXISTS uq_user_account_id_tenant")


def _add_resource_integrity(table: str) -> None:
    op.execute(
        f"""
        ALTER TABLE {table}
            ADD CONSTRAINT fk_{table}_owner_tenant
            FOREIGN KEY (owner_id, tenant_id)
            REFERENCES user_account (id, tenant_id)
        """
    )
    op.execute(
        f"""
        ALTER TABLE {table}
            ADD CONSTRAINT fk_{table}_department_tenant
            FOREIGN KEY (department_id, tenant_id)
            REFERENCES department (id, tenant_id)
        """
    )


def _drop_resource_integrity(table: str) -> None:
    op.execute(
        f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS fk_{table}_department_tenant"
    )
    op.execute(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS fk_{table}_owner_tenant")


def _create_group_member_tenant_trigger() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION enforce_user_group_member_tenant_integrity()
        RETURNS trigger AS $$
        DECLARE
            user_tenant UUID;
            group_tenant UUID;
        BEGIN
            SELECT tenant_id INTO user_tenant FROM user_account WHERE id = NEW.user_id;
            SELECT tenant_id INTO group_tenant FROM user_group WHERE id = NEW.group_id;
            IF user_tenant IS NULL
                OR group_tenant IS NULL
                OR user_tenant <> group_tenant
                OR NEW.tenant_id <> user_tenant THEN
                RAISE EXCEPTION 'user_group_member tenant mismatch';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        DROP TRIGGER IF EXISTS trg_user_group_member_tenant_integrity
            ON user_group_member
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_user_group_member_tenant_integrity
            BEFORE INSERT OR UPDATE ON user_group_member
            FOR EACH ROW EXECUTE FUNCTION enforce_user_group_member_tenant_integrity()
        """
    )


def _create_user_role_tenant_trigger() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION enforce_user_role_tenant_integrity()
        RETURNS trigger AS $$
        DECLARE
            user_tenant UUID;
            role_tenant UUID;
            role_system BOOLEAN;
        BEGIN
            SELECT tenant_id INTO user_tenant FROM user_account WHERE id = NEW.user_id;
            SELECT tenant_id, is_system INTO role_tenant, role_system FROM role WHERE id = NEW.role_id;
            IF user_tenant IS NULL OR role_system IS NULL THEN
                RAISE EXCEPTION 'user_role missing user or role';
            END IF;
            IF NOT role_system AND role_tenant <> user_tenant THEN
                RAISE EXCEPTION 'user_role tenant mismatch';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute("DROP TRIGGER IF EXISTS trg_user_role_tenant_integrity ON user_role")
    op.execute(
        """
        CREATE TRIGGER trg_user_role_tenant_integrity
            BEFORE INSERT OR UPDATE ON user_role
            FOR EACH ROW EXECUTE FUNCTION enforce_user_role_tenant_integrity()
        """
    )


def _add_user_group_member_tenant_id() -> None:
    op.execute("ALTER TABLE user_group_member ADD COLUMN IF NOT EXISTS tenant_id UUID")
    op.execute(
        """
        UPDATE user_group_member ugm
        SET tenant_id = ug.tenant_id
        FROM user_group ug
        WHERE ug.id = ugm.group_id AND ugm.tenant_id IS NULL
        """
    )
    op.execute("ALTER TABLE user_group_member ALTER COLUMN tenant_id SET NOT NULL")
    op.execute(
        """
        ALTER TABLE user_group_member
            ADD CONSTRAINT fk_user_group_member_tenant_id
            FOREIGN KEY (tenant_id) REFERENCES tenant (id) ON DELETE CASCADE
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_user_group_member_tenant_id "
        "ON user_group_member (tenant_id)"
    )
    op.execute(
        "ALTER TABLE user_group_member DROP CONSTRAINT IF EXISTS uq_user_group_member"
    )
    op.execute(
        """
        ALTER TABLE user_group_member
            ADD CONSTRAINT uq_user_group_member UNIQUE (tenant_id, user_id, group_id)
        """
    )


def _drop_user_group_member_tenant_id() -> None:
    op.execute(
        "ALTER TABLE user_group_member DROP CONSTRAINT IF EXISTS uq_user_group_member"
    )
    op.execute(
        """
        ALTER TABLE user_group_member
            ADD CONSTRAINT uq_user_group_member UNIQUE (user_id, group_id)
        """
    )
    op.execute("DROP INDEX IF EXISTS ix_user_group_member_tenant_id")
    op.execute(
        "ALTER TABLE user_group_member DROP CONSTRAINT IF EXISTS "
        "fk_user_group_member_tenant_id"
    )
    op.execute("ALTER TABLE user_group_member DROP COLUMN IF EXISTS tenant_id")


def _enable_tenant_rls(table: str) -> None:
    policy = f"{table}_tenant_isolation"
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    op.execute(f"DROP POLICY IF EXISTS {policy} ON {table}")
    op.execute(
        f"""
        CREATE POLICY {policy} ON {table}
        FOR ALL
        USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
        WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
        """
    )


def _disable_tenant_rls(table: str) -> None:
    policy = f"{table}_tenant_isolation"
    op.execute(f"DROP POLICY IF EXISTS {policy} ON {table}")
    op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")


def _add_kg_child_rls(table: str) -> None:
    policy = f"{table}_tenant_isolation"
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    op.execute(f"DROP POLICY IF EXISTS {policy} ON {table}")
    op.execute(
        f"""
        CREATE POLICY {policy} ON {table}
        FOR ALL
        USING (
            EXISTS (
                SELECT 1 FROM knowledge_graphs kg
                WHERE kg.id = {table}.graph_id
                  AND kg.tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
            )
        )
        WITH CHECK (
            EXISTS (
                SELECT 1 FROM knowledge_graphs kg
                WHERE kg.id = {table}.graph_id
                  AND kg.tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid
            )
        )
        """
    )


def _drop_kg_child_rls(table: str) -> None:
    policy = f"{table}_tenant_isolation"
    op.execute(f"DROP POLICY IF EXISTS {policy} ON {table}")
    op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
