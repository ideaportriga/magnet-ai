# type: ignore
"""Register ``delete:files`` permission and grant it to the system admin role.

Until now ``FilesController`` had no permission guards at all — anyone
authenticated could list, download, or delete files. We're locking it
down with ``read:files`` / ``write:files`` / ``delete:files`` per route;
the first two are already in the catalog (since b4c5d6e7f8a9), the
delete code is new.

Revision ID: b1c2d3e4f5a6
Revises: z0a1b2c3d4e5
Create Date: 2026-05-21 01:05:00.000000+00:00
"""

from __future__ import annotations

import warnings

from alembic import op

__all__ = ["downgrade", "upgrade", "schema_upgrades", "schema_downgrades"]

revision = "b1c2d3e4f5a6"
down_revision = "z0a1b2c3d4e5"
branch_labels = None
depends_on = None


_NEW_CODE = "delete:files"


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
    op.execute(
        f"""
        INSERT INTO permission
            (id, code, resource_type, action, description, is_system, created_at, updated_at)
        VALUES
            (gen_random_uuid(), '{_NEW_CODE}', 'files', 'delete', 'Delete files', TRUE, NOW(), NOW())
        ON CONFLICT (code) DO UPDATE SET
            resource_type = EXCLUDED.resource_type,
            action = EXCLUDED.action,
            description = EXCLUDED.description,
            is_system = TRUE,
            updated_at = NOW()
        """
    )
    # System admin gets every code by definition. tenant_id stays NULL
    # for system-role grants (matches existing rows).
    op.execute(
        f"""
        INSERT INTO role_permission (id, role_id, permission_code, created_at, updated_at)
        SELECT gen_random_uuid(), r.id, '{_NEW_CODE}', NOW(), NOW()
        FROM role r
        WHERE r.slug = 'admin' AND r.is_system = TRUE
        ON CONFLICT (role_id, permission_code) DO NOTHING
        """
    )


def schema_downgrades() -> None:
    op.execute(f"DELETE FROM role_permission WHERE permission_code = '{_NEW_CODE}'")
    op.execute(f"DELETE FROM permission WHERE code = '{_NEW_CODE}'")
