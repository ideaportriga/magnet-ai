# type: ignore
"""Access audit log table.

Records every mutation to access-control state (role CRUD, user-role
assign/revoke, resource grants). Tenant-scoped. PR 5 of the access-control
plan.

Revision ID: d6e7f8a9b0c1
Revises: c5d6e7f8a9b0
Create Date: 2026-05-15 11:00:00.000000+00:00
"""

from __future__ import annotations

import warnings

from alembic import op

__all__ = ["downgrade", "upgrade", "schema_upgrades", "schema_downgrades"]

revision = "d6e7f8a9b0c1"
down_revision = "c5d6e7f8a9b0"
branch_labels = None
depends_on = None


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
        """
        CREATE TABLE IF NOT EXISTS access_audit_log (
            id UUID NOT NULL,
            tenant_id UUID NOT NULL,
            actor_id UUID,
            action VARCHAR(100) NOT NULL,
            target_type VARCHAR(100) NOT NULL,
            target_id UUID,
            payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            sa_orm_sentinel INTEGER,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
            CONSTRAINT pk_access_audit_log PRIMARY KEY (id),
            CONSTRAINT fk_access_audit_log_tenant_id FOREIGN KEY (tenant_id)
                REFERENCES tenant (id) ON DELETE CASCADE,
            CONSTRAINT fk_access_audit_log_actor_id FOREIGN KEY (actor_id)
                REFERENCES user_account (id) ON DELETE SET NULL
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_access_audit_log_tenant_id "
        "ON access_audit_log (tenant_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_access_audit_log_actor_id "
        "ON access_audit_log (actor_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_access_audit_log_action "
        "ON access_audit_log (action)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_access_audit_log_tenant_created "
        "ON access_audit_log (tenant_id, created_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_access_audit_log_tenant_actor_created "
        "ON access_audit_log (tenant_id, actor_id, created_at)"
    )


def schema_downgrades() -> None:
    op.execute("DROP INDEX IF EXISTS ix_access_audit_log_tenant_actor_created")
    op.execute("DROP INDEX IF EXISTS ix_access_audit_log_tenant_created")
    op.execute("DROP INDEX IF EXISTS ix_access_audit_log_action")
    op.execute("DROP INDEX IF EXISTS ix_access_audit_log_actor_id")
    op.execute("DROP INDEX IF EXISTS ix_access_audit_log_tenant_id")
    op.execute("DROP TABLE IF EXISTS access_audit_log")
