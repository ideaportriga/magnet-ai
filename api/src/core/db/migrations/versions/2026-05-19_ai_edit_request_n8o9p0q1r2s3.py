# type: ignore
"""AI edit request tracking table + ai_request_id on entity_audit_log.

Part B of ``docs/AI_ENTITY_EDITING_PLAN.md``. The table records every
call to the AI entity editor (succeeded, schema-invalid, llm-error); the
column on ``entity_audit_log`` links audit rows produced by an applied
AI edit back to the original request.

Revision ID: n8o9p0q1r2s3
Revises: m7n8o9p0q1r2
Create Date: 2026-05-19 19:00:00.000000+00:00
"""

from __future__ import annotations

import warnings

from alembic import op

__all__ = ["downgrade", "upgrade", "schema_upgrades", "schema_downgrades"]

revision = "n8o9p0q1r2s3"
down_revision = "m7n8o9p0q1r2"
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
        INSERT INTO permission
            (id, code, resource_type, action, description, is_system, created_at, updated_at)
        VALUES
            (gen_random_uuid(), 'restore:audit', 'audit', 'restore', 'Restore entities from audit history', TRUE, NOW(), NOW()),
            (gen_random_uuid(), 'execute:ai_edit', 'ai_edit', 'execute', 'Generate AI-assisted entity edits', TRUE, NOW(), NOW())
        ON CONFLICT (code) DO UPDATE SET
            resource_type = EXCLUDED.resource_type,
            action = EXCLUDED.action,
            description = EXCLUDED.description,
            is_system = TRUE,
            updated_at = NOW()
        """
    )
    op.execute(
        """
        INSERT INTO role_permission (id, role_id, permission_code, created_at, updated_at)
        SELECT gen_random_uuid(), r.id, p.code, NOW(), NOW()
        FROM role r
        CROSS JOIN (VALUES ('restore:audit'), ('execute:ai_edit')) AS p(code)
        WHERE r.slug = 'admin' AND r.is_system = TRUE
        ON CONFLICT (role_id, permission_code) DO NOTHING
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_edit_request (
            id UUID NOT NULL,
            tenant_id UUID NOT NULL,
            actor_id UUID,
            entity_type VARCHAR(100) NOT NULL,
            entity_id UUID NOT NULL,
            instruction TEXT NOT NULL,
            model VARCHAR(255),
            status VARCHAR(20) NOT NULL DEFAULT 'succeeded',
            error_message TEXT,
            prompt_tokens INTEGER NOT NULL DEFAULT 0,
            completion_tokens INTEGER NOT NULL DEFAULT 0,
            total_tokens INTEGER NOT NULL DEFAULT 0,
            cost_usd NUMERIC(12, 6) NOT NULL DEFAULT 0,
            latency_ms INTEGER NOT NULL DEFAULT 0,
            snapshot_before JSONB,
            snapshot_after JSONB,
            sa_orm_sentinel INTEGER,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
            CONSTRAINT pk_ai_edit_request PRIMARY KEY (id),
            CONSTRAINT fk_ai_edit_request_tenant_id FOREIGN KEY (tenant_id)
                REFERENCES tenant (id) ON DELETE CASCADE,
            CONSTRAINT fk_ai_edit_request_actor_id FOREIGN KEY (actor_id)
                REFERENCES user_account (id) ON DELETE SET NULL
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_ai_edit_request_tenant_id "
        "ON ai_edit_request (tenant_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_ai_edit_request_actor_id "
        "ON ai_edit_request (actor_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_ai_edit_request_entity_type "
        "ON ai_edit_request (entity_type)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_ai_edit_request_entity_id "
        "ON ai_edit_request (entity_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_ai_edit_request_tenant_created "
        "ON ai_edit_request (tenant_id, created_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_ai_edit_request_tenant_actor_created "
        "ON ai_edit_request (tenant_id, actor_id, created_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_ai_edit_request_tenant_entity "
        "ON ai_edit_request (tenant_id, entity_type, entity_id)"
    )

    # Bridge column: an audit row written by an AI-driven save points back
    # to its originating request. Nullable — manual edits leave it NULL.
    op.execute(
        """
        ALTER TABLE entity_audit_log
        ADD COLUMN IF NOT EXISTS ai_request_id UUID
            REFERENCES ai_edit_request (id) ON DELETE SET NULL
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_entity_audit_log_ai_request_id "
        "ON entity_audit_log (ai_request_id)"
    )


def schema_downgrades() -> None:
    op.execute("DROP INDEX IF EXISTS ix_entity_audit_log_ai_request_id")
    op.execute("ALTER TABLE entity_audit_log DROP COLUMN IF EXISTS ai_request_id")

    op.execute("DROP INDEX IF EXISTS ix_ai_edit_request_tenant_entity")
    op.execute("DROP INDEX IF EXISTS ix_ai_edit_request_tenant_actor_created")
    op.execute("DROP INDEX IF EXISTS ix_ai_edit_request_tenant_created")
    op.execute("DROP INDEX IF EXISTS ix_ai_edit_request_entity_id")
    op.execute("DROP INDEX IF EXISTS ix_ai_edit_request_entity_type")
    op.execute("DROP INDEX IF EXISTS ix_ai_edit_request_actor_id")
    op.execute("DROP INDEX IF EXISTS ix_ai_edit_request_tenant_id")
    op.execute("DROP TABLE IF EXISTS ai_edit_request")

    op.execute(
        "DELETE FROM role_permission WHERE permission_code IN ('restore:audit', 'execute:ai_edit')"
    )
    op.execute(
        "DELETE FROM permission WHERE code IN ('restore:audit', 'execute:ai_edit')"
    )
