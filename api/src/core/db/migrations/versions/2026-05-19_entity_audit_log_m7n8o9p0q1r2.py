# type: ignore
"""Entity audit log table — per-entity history with restore support.

Part A.P1 of ``docs/AI_ENTITY_EDITING_PLAN.md``. Separate from
``access_audit_log`` (which tracks access-control state); this table
records create/update/delete/restore of business entities such as
agents, prompts, RAG tools, etc.

Revision ID: m7n8o9p0q1r2
Revises: l6m7n8o9p0q1
Create Date: 2026-05-19 18:00:00.000000+00:00
"""

from __future__ import annotations

import warnings

from alembic import op

__all__ = ["downgrade", "upgrade", "schema_upgrades", "schema_downgrades"]

revision = "m7n8o9p0q1r2"
down_revision = "l6m7n8o9p0q1"
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
        CREATE TABLE IF NOT EXISTS entity_audit_log (
            id UUID NOT NULL,
            tenant_id UUID NOT NULL,
            entity_type VARCHAR(100) NOT NULL,
            entity_id UUID NOT NULL,
            action VARCHAR(20) NOT NULL,
            actor_id UUID,
            actor_type VARCHAR(20) NOT NULL,
            actor_display VARCHAR(255) NOT NULL DEFAULT '',
            source VARCHAR(30) NOT NULL DEFAULT 'system',
            request_id VARCHAR(100),
            snapshot_before JSONB,
            snapshot_after JSONB,
            diff JSONB NOT NULL DEFAULT '{}'::jsonb,
            sa_orm_sentinel INTEGER,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
            CONSTRAINT pk_entity_audit_log PRIMARY KEY (id),
            CONSTRAINT fk_entity_audit_log_tenant_id FOREIGN KEY (tenant_id)
                REFERENCES tenant (id) ON DELETE CASCADE,
            CONSTRAINT fk_entity_audit_log_actor_id FOREIGN KEY (actor_id)
                REFERENCES user_account (id) ON DELETE SET NULL
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_entity_audit_log_tenant_id "
        "ON entity_audit_log (tenant_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_entity_audit_log_entity_type "
        "ON entity_audit_log (entity_type)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_entity_audit_log_entity_id "
        "ON entity_audit_log (entity_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_entity_audit_log_actor_id "
        "ON entity_audit_log (actor_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_entity_audit_log_action "
        "ON entity_audit_log (action)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_entity_audit_log_tenant_entity_created "
        "ON entity_audit_log (tenant_id, entity_type, entity_id, created_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_entity_audit_log_tenant_created "
        "ON entity_audit_log (tenant_id, created_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_entity_audit_log_tenant_actor_created "
        "ON entity_audit_log (tenant_id, actor_id, created_at)"
    )


def schema_downgrades() -> None:
    op.execute("DROP INDEX IF EXISTS ix_entity_audit_log_tenant_actor_created")
    op.execute("DROP INDEX IF EXISTS ix_entity_audit_log_tenant_created")
    op.execute("DROP INDEX IF EXISTS ix_entity_audit_log_tenant_entity_created")
    op.execute("DROP INDEX IF EXISTS ix_entity_audit_log_action")
    op.execute("DROP INDEX IF EXISTS ix_entity_audit_log_actor_id")
    op.execute("DROP INDEX IF EXISTS ix_entity_audit_log_entity_id")
    op.execute("DROP INDEX IF EXISTS ix_entity_audit_log_entity_type")
    op.execute("DROP INDEX IF EXISTS ix_entity_audit_log_tenant_id")
    op.execute("DROP TABLE IF EXISTS entity_audit_log")
