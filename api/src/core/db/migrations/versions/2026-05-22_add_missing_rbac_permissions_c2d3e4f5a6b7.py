# type: ignore
"""Register missing RBAC permission codes and grant them to system roles.

Closes the 2nd-level (role × permission) gaps found during the
2026-05-22 audit. Several controllers had no `require_permission(...)`
guard at all; this migration adds the codes they will now require so
the catalog stays in sync with the `guards.permissions.Permission` enum.

New codes:
  - delete:evaluations, delete:deep_research, delete:prompt_queue
  - delete:jobs, delete:note_taker, delete:ai_models, delete:providers
  - delete:api_keys
  - write:observability, read:metrics, write:metrics, delete:metrics
  - read:traces, write:traces, delete:traces
  - read:catalog
  - read:oauth_clients, write:oauth_clients, delete:oauth_clients
  - manage:scheduler

System role grants:
  - admin: every new code
  - user: read:catalog, read:providers (so the regular user catalog
    page keeps working once the new gates are enforced)
  - viewer: read:catalog, read:metrics, read:traces, read:oauth_clients,
    read:providers (viewer is read-everything by definition; existing
    "viewer gets every read:* code" contract is preserved)

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-05-22 09:00:00.000000+00:00
"""

from __future__ import annotations

import warnings

from alembic import op

__all__ = ["downgrade", "upgrade", "schema_upgrades", "schema_downgrades"]

revision = "c2d3e4f5a6b7"
down_revision = "b1c2d3e4f5a6"
branch_labels = None
depends_on = None


NEW_PERMISSIONS: list[tuple[str, str, str, str]] = [
    # (code, resource_type, action, description)
    ("delete:evaluations", "evaluations", "delete", "Delete evaluation sets and runs"),
    (
        "delete:deep_research",
        "deep_research",
        "delete",
        "Delete deep research configs/runs",
    ),
    ("delete:prompt_queue", "prompt_queue", "delete", "Delete prompt queue configs"),
    ("delete:jobs", "jobs", "delete", "Delete jobs"),
    ("delete:note_taker", "note_taker", "delete", "Delete note taker sessions"),
    ("delete:ai_models", "ai_models", "delete", "Delete AI models"),
    ("delete:providers", "providers", "delete", "Delete providers"),
    ("delete:api_keys", "api_keys", "delete", "Delete API keys"),
    (
        "write:observability",
        "observability",
        "write",
        "Write observability feedback / annotations",
    ),
    ("read:metrics", "metrics", "read", "View metrics"),
    ("write:metrics", "metrics", "write", "Create or modify metrics"),
    ("delete:metrics", "metrics", "delete", "Delete metrics"),
    ("read:traces", "traces", "read", "View traces"),
    ("write:traces", "traces", "write", "Create or modify traces"),
    ("delete:traces", "traces", "delete", "Delete traces"),
    ("read:catalog", "catalog", "read", "View the cross-resource catalog"),
    ("read:oauth_clients", "oauth_clients", "read", "View OAuth (MCP) clients"),
    (
        "write:oauth_clients",
        "oauth_clients",
        "write",
        "Create or modify OAuth (MCP) clients",
    ),
    ("delete:oauth_clients", "oauth_clients", "delete", "Delete OAuth (MCP) clients"),
    ("manage:scheduler", "scheduler", "manage", "Schedule / cancel background jobs"),
]


# Codes that should land in the regular `user` role on top of admin.
_USER_GRANTS = [
    "read:catalog",
    "read:providers",
]

# Codes that should land in the viewer role (everything read:*).
_VIEWER_GRANTS = [
    "read:catalog",
    "read:metrics",
    "read:traces",
    "read:oauth_clients",
    "read:providers",
]


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
    for code, resource_type, action, description in NEW_PERMISSIONS:
        op.execute(
            f"""
            INSERT INTO permission
                (id, code, resource_type, action, description, is_system, created_at, updated_at)
            VALUES
                (gen_random_uuid(), '{code}', '{resource_type}', '{action}',
                 '{description.replace("'", "''")}', TRUE, NOW(), NOW())
            ON CONFLICT (code) DO UPDATE SET
                resource_type = EXCLUDED.resource_type,
                action = EXCLUDED.action,
                description = EXCLUDED.description,
                is_system = TRUE,
                updated_at = NOW()
            """
        )

    # Admin gets every new code.
    for code, *_ in NEW_PERMISSIONS:
        op.execute(
            f"""
            INSERT INTO role_permission (id, role_id, permission_code, created_at, updated_at)
            SELECT gen_random_uuid(), r.id, '{code}', NOW(), NOW()
            FROM role r
            WHERE r.slug = 'admin' AND r.is_system = TRUE
            ON CONFLICT (role_id, permission_code) DO NOTHING
            """
        )

    for code in _USER_GRANTS:
        op.execute(
            f"""
            INSERT INTO role_permission (id, role_id, permission_code, created_at, updated_at)
            SELECT gen_random_uuid(), r.id, '{code}', NOW(), NOW()
            FROM role r
            WHERE r.slug = 'user' AND r.is_system = TRUE
            ON CONFLICT (role_id, permission_code) DO NOTHING
            """
        )

    for code in _VIEWER_GRANTS:
        op.execute(
            f"""
            INSERT INTO role_permission (id, role_id, permission_code, created_at, updated_at)
            SELECT gen_random_uuid(), r.id, '{code}', NOW(), NOW()
            FROM role r
            WHERE r.slug = 'viewer' AND r.is_system = TRUE
            ON CONFLICT (role_id, permission_code) DO NOTHING
            """
        )


def schema_downgrades() -> None:
    codes = [row[0] for row in NEW_PERMISSIONS]
    placeholder = ", ".join(f"'{c}'" for c in codes)
    op.execute(f"DELETE FROM role_permission WHERE permission_code IN ({placeholder})")
    op.execute(f"DELETE FROM permission WHERE code IN ({placeholder})")
