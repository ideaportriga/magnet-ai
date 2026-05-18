# type: ignore
"""DB-backed permission catalog: permission/role_permission tables + role.is_system.

Implements PR 2 of `docs/access-control-tenancy-plan-v2.md`.

Adds:
  - role.is_system column (NOT NULL, default false)
  - permission catalog table
  - role_permission association table
  - seed: permission catalog rows + system role grants (admin/user/viewer)
  - upserts the `viewer` system role if missing

Custom tenant roles, role.tenant_id, and admin UI ship in PR 4/5.

Revision ID: b4c5d6e7f8a9
Revises: a4b5c6d7e8f9
Create Date: 2026-05-15 09:00:00.000000+00:00
"""

from __future__ import annotations

import warnings

from alembic import op

__all__ = ["downgrade", "upgrade", "schema_upgrades", "schema_downgrades"]

revision = "b4c5d6e7f8a9"
# Linearize after the most recent non-access-control head (PR 2 of the
# access-control plan is the start of a new chain that follows
# notetaker reliability work).
down_revision = "a4b5c6d7e8f9"
branch_labels = None
depends_on = None


# ---------------------------------------------------------------------------
# Catalog snapshot (frozen as of 2026-05-15).
#
# Source of truth is `guards.permissions.Permission`. The migration must keep
# its OWN copy so it stays reproducible if the enum changes later. Any future
# code change to the enum requires a new migration that adds/renames rows.
# ---------------------------------------------------------------------------

PERMISSIONS: list[tuple[str, str, str, str]] = [
    # (code, resource_type, action, description)
    ("read:agents", "agents", "read", "View agents"),
    ("write:agents", "agents", "write", "Create or modify agents"),
    ("delete:agents", "agents", "delete", "Delete agents"),
    ("execute:agents", "agents", "execute", "Run / test agents"),
    ("share:agents", "agents", "share", "Share agents with other users"),
    ("read:ai_apps", "ai_apps", "read", "View AI apps"),
    ("write:ai_apps", "ai_apps", "write", "Create or modify AI apps"),
    ("delete:ai_apps", "ai_apps", "delete", "Delete AI apps"),
    ("read:collections", "collections", "read", "View collections"),
    ("write:collections", "collections", "write", "Create or modify collections"),
    ("delete:collections", "collections", "delete", "Delete collections"),
    ("read:prompts", "prompts", "read", "View prompt templates"),
    ("write:prompts", "prompts", "write", "Create or modify prompt templates"),
    ("delete:prompts", "prompts", "delete", "Delete prompt templates"),
    ("read:knowledge_graph", "knowledge_graph", "read", "View knowledge graphs"),
    ("write:knowledge_graph", "knowledge_graph", "write", "Modify knowledge graphs"),
    ("delete:knowledge_graph", "knowledge_graph", "delete", "Delete knowledge graphs"),
    ("read:rag_tools", "rag_tools", "read", "View RAG tools"),
    ("write:rag_tools", "rag_tools", "write", "Create or modify RAG tools"),
    ("delete:rag_tools", "rag_tools", "delete", "Delete RAG tools"),
    ("read:retrieval_tools", "retrieval_tools", "read", "View retrieval tools"),
    (
        "write:retrieval_tools",
        "retrieval_tools",
        "write",
        "Create or modify retrieval tools",
    ),
    ("delete:retrieval_tools", "retrieval_tools", "delete", "Delete retrieval tools"),
    ("read:mcp_servers", "mcp_servers", "read", "View MCP servers"),
    ("write:mcp_servers", "mcp_servers", "write", "Create or modify MCP servers"),
    ("delete:mcp_servers", "mcp_servers", "delete", "Delete MCP servers"),
    ("read:api_servers", "api_servers", "read", "View API servers"),
    ("write:api_servers", "api_servers", "write", "Create or modify API servers"),
    ("delete:api_servers", "api_servers", "delete", "Delete API servers"),
    ("read:evaluations", "evaluations", "read", "View evaluation sets and runs"),
    ("write:evaluations", "evaluations", "write", "Create or modify evaluations"),
    ("read:deep_research", "deep_research", "read", "View deep research configs/runs"),
    ("write:deep_research", "deep_research", "write", "Run / modify deep research"),
    ("read:prompt_queue", "prompt_queue", "read", "View prompt queue"),
    ("write:prompt_queue", "prompt_queue", "write", "Modify prompt queue"),
    ("read:files", "files", "read", "View files"),
    ("write:files", "files", "write", "Upload / modify files"),
    ("read:jobs", "jobs", "read", "View background jobs"),
    ("write:jobs", "jobs", "write", "Trigger / cancel jobs"),
    ("read:observability", "observability", "read", "View traces, metrics, logs"),
    ("read:note_taker", "note_taker", "read", "View note taker sessions"),
    ("write:note_taker", "note_taker", "write", "Modify note taker settings/jobs"),
    ("read:ai_models", "ai_models", "read", "View AI models"),
    ("write:ai_models", "ai_models", "write", "Modify AI models"),
    ("read:providers", "providers", "read", "View providers"),
    ("write:providers", "providers", "write", "Modify providers"),
    ("read:settings", "settings", "read", "View settings"),
    ("write:settings", "settings", "write", "Modify settings"),
    ("read:roles", "roles", "read", "View roles and permission matrix"),
    ("write:roles", "roles", "write", "Create / edit / delete custom roles"),
    ("read:users", "users", "read", "View user list"),
    ("manage:users", "users", "manage", "Assign / revoke roles, departments, groups"),
    ("read:groups", "groups", "read", "View groups"),
    ("write:groups", "groups", "write", "Create or modify groups"),
    ("read:api_keys", "api_keys", "read", "View API keys"),
    ("write:api_keys", "api_keys", "write", "Create or revoke API keys"),
    ("manage:resource_access", "resource_access", "manage", "Manage record-level ACLs"),
    ("read:audit", "audit", "read", "View access audit log"),
]


_ALL_CODES = [c for c, *_ in PERMISSIONS]
_READ_CODES = [c for c, _r, action, _d in PERMISSIONS if action == "read"]

# `user` system role: commodity actions for end users (read most things,
# execute agents, manage own files / note taker). Mirrors
# guards.permissions.SYSTEM_ROLE_DEFAULTS["user"].
_USER_CODES = [
    "read:agents",
    "execute:agents",
    "read:ai_apps",
    "read:collections",
    "read:prompts",
    "read:knowledge_graph",
    "read:rag_tools",
    "read:retrieval_tools",
    "read:mcp_servers",
    "read:api_servers",
    "read:files",
    "write:files",
    "read:jobs",
    "read:ai_models",
    "read:note_taker",
    "write:note_taker",
]

SYSTEM_ROLE_DEFAULTS: dict[str, list[str]] = {
    "admin": _ALL_CODES,
    "user": _USER_CODES,
    "viewer": _READ_CODES,
}


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
    # 1. role.is_system column
    op.execute("""
        ALTER TABLE role
            ADD COLUMN IF NOT EXISTS is_system BOOLEAN NOT NULL DEFAULT FALSE
    """)
    op.execute("""
        UPDATE role
        SET is_system = TRUE
        WHERE slug IN ('admin', 'user', 'viewer')
    """)

    # 2. Make sure the `viewer` system role exists (initial migration only
    #    seeded admin and user). Idempotent.
    op.execute("""
        INSERT INTO role (id, name, slug, description, is_system, created_at, updated_at)
        VALUES (
            gen_random_uuid(),
            'Viewer',
            'viewer',
            'Read-only access across the platform',
            TRUE,
            NOW(),
            NOW()
        )
        ON CONFLICT (slug) DO UPDATE SET is_system = TRUE
    """)

    # 3. permission catalog
    op.execute("""
        CREATE TABLE IF NOT EXISTS permission (
            id UUID NOT NULL,
            code VARCHAR(100) NOT NULL,
            resource_type VARCHAR(100) NOT NULL,
            action VARCHAR(50) NOT NULL,
            description TEXT,
            is_system BOOLEAN NOT NULL DEFAULT TRUE,
            sa_orm_sentinel INTEGER,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
            CONSTRAINT pk_permission PRIMARY KEY (id),
            CONSTRAINT uq_permission_code UNIQUE (code)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_permission_code ON permission (code)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_permission_resource_type ON permission (resource_type)"
    )

    # 4. role_permission association
    op.execute("""
        CREATE TABLE IF NOT EXISTS role_permission (
            id UUID NOT NULL,
            role_id UUID NOT NULL,
            permission_code VARCHAR(100) NOT NULL,
            sa_orm_sentinel INTEGER,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
            CONSTRAINT pk_role_permission PRIMARY KEY (id),
            CONSTRAINT fk_role_permission_role_id FOREIGN KEY (role_id)
                REFERENCES role (id) ON DELETE CASCADE,
            CONSTRAINT fk_role_permission_permission_code FOREIGN KEY (permission_code)
                REFERENCES permission (code) ON DELETE CASCADE,
            CONSTRAINT uq_role_permission UNIQUE (role_id, permission_code)
        )
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_role_permission_role_id ON role_permission (role_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_role_permission_permission_code "
        "ON role_permission (permission_code)"
    )

    # 5. Seed permission catalog (idempotent)
    for code, resource_type, action, description in PERMISSIONS:
        op.execute(
            "INSERT INTO permission "
            "(id, code, resource_type, action, description, is_system, created_at, updated_at) "
            f"VALUES (gen_random_uuid(), '{code}', '{resource_type}', '{action}', "
            f"{_q(description)}, TRUE, NOW(), NOW()) "
            "ON CONFLICT (code) DO UPDATE SET "
            "resource_type = EXCLUDED.resource_type, "
            "action = EXCLUDED.action, "
            "description = EXCLUDED.description, "
            "is_system = TRUE, "
            "updated_at = NOW()"
        )

    # 6. Seed role_permission grants for system roles (idempotent)
    for role_slug, codes in SYSTEM_ROLE_DEFAULTS.items():
        for code in codes:
            op.execute(
                "INSERT INTO role_permission "
                "(id, role_id, permission_code, created_at, updated_at) "
                f"SELECT gen_random_uuid(), r.id, '{code}', NOW(), NOW() "
                f"FROM role r WHERE r.slug = '{role_slug}' AND r.is_system = TRUE "
                "ON CONFLICT (role_id, permission_code) DO NOTHING"
            )


def schema_downgrades() -> None:
    op.execute("DROP INDEX IF EXISTS ix_role_permission_permission_code")
    op.execute("DROP INDEX IF EXISTS ix_role_permission_role_id")
    op.execute("DROP TABLE IF EXISTS role_permission")

    op.execute("DROP INDEX IF EXISTS ix_permission_resource_type")
    op.execute("DROP INDEX IF EXISTS ix_permission_code")
    op.execute("DROP TABLE IF EXISTS permission")

    op.execute("ALTER TABLE role DROP COLUMN IF EXISTS is_system")


def _q(value: str | None) -> str:
    """Quote a SQL string literal with naive single-quote escaping.

    Permission descriptions are checked-in literals, no user input — but be
    polite anyway.
    """
    if value is None:
        return "NULL"
    escaped = value.replace("'", "''")
    return f"'{escaped}'"
