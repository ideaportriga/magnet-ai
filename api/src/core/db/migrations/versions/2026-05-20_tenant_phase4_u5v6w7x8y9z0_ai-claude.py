# type: ignore
"""Tenant-isolation Phase 4 — Slack & Teams webhook tables.

These are populated from inbound webhook payloads, so the auth middleware
context is not set when the row is inserted. The accompanying handler
code (slack OAuth callback, Teams Graph webhook) must resolve the tenant
from the payload BEFORE the insert.

Tables:

  slack_installations   — NOT NULL tenant_id, backfill via agents.system_name.
  slack_oauth_states    — NOT NULL tenant_id, backfill via agents.system_name.
  teams_meeting         — NULLABLE tenant_id. Backfill via
                          note_taker_settings.system_name where possible.
                          Rows attached to a tenant via the bot install
                          flow will become NOT NULL going forward (enforced
                          by handler), but legacy rows may remain NULL.
                          Policy: IS NULL OR match.
  teams_user            — NULLABLE tenant_id. Backfill via the user's
                          aad_object_id matched to user_account_oauth.
                          Policy: IS NULL OR match.
  teams_webhook_event   — NULLABLE tenant_id. Backfill via the parent
                          teams_meeting (after teams_meeting tenant_id is
                          set). Policy: IS NULL OR match.

Revision ID: u5v6w7x8y9z0
Revises: t4u5v6w7x8y9
Create Date: 2026-05-20 22:00:00.000000+00:00
"""

from __future__ import annotations

import warnings

from alembic import op

__all__ = ["downgrade", "upgrade", "schema_upgrades", "schema_downgrades"]

revision = "u5v6w7x8y9z0"
down_revision = "t4u5v6w7x8y9"
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


def _enable_rls(table: str) -> None:
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")


def _disable_rls(table: str) -> None:
    op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")


def _attach_policy(table: str, using_expr: str) -> None:
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
    # ── slack_installations (NOT NULL via agents.system_name) ──────────
    op.execute(
        "ALTER TABLE slack_installations ADD COLUMN IF NOT EXISTS tenant_id UUID"
    )
    op.execute(
        """
        UPDATE slack_installations s
        SET tenant_id = a.tenant_id
        FROM agents a
        WHERE s.tenant_id IS NULL
          AND a.system_name = s.agent_system_name
        """
    )
    op.execute("DELETE FROM slack_installations WHERE tenant_id IS NULL")
    op.execute("ALTER TABLE slack_installations ALTER COLUMN tenant_id SET NOT NULL")
    op.execute(
        """
        ALTER TABLE slack_installations
            ADD CONSTRAINT fk_slack_installations_tenant_id
            FOREIGN KEY (tenant_id) REFERENCES tenant (id) ON DELETE CASCADE
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_slack_installations_tenant_id "
        "ON slack_installations (tenant_id)"
    )
    _enable_rls("slack_installations")
    _attach_policy("slack_installations", _STANDARD_USING)

    # ── slack_oauth_states (NOT NULL via agents.system_name) ───────────
    op.execute("ALTER TABLE slack_oauth_states ADD COLUMN IF NOT EXISTS tenant_id UUID")
    op.execute(
        """
        UPDATE slack_oauth_states s
        SET tenant_id = a.tenant_id
        FROM agents a
        WHERE s.tenant_id IS NULL
          AND a.system_name = s.agent_system_name
        """
    )
    # OAuth states are short-lived (TTL). Drop any unmappable rows.
    op.execute("DELETE FROM slack_oauth_states WHERE tenant_id IS NULL")
    op.execute("ALTER TABLE slack_oauth_states ALTER COLUMN tenant_id SET NOT NULL")
    op.execute(
        """
        ALTER TABLE slack_oauth_states
            ADD CONSTRAINT fk_slack_oauth_states_tenant_id
            FOREIGN KEY (tenant_id) REFERENCES tenant (id) ON DELETE CASCADE
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_slack_oauth_states_tenant_id "
        "ON slack_oauth_states (tenant_id)"
    )
    _enable_rls("slack_oauth_states")
    _attach_policy("slack_oauth_states", _STANDARD_USING)

    # ── teams_meeting (NULLABLE via note_taker_settings.system_name) ───
    op.execute("ALTER TABLE teams_meeting ADD COLUMN IF NOT EXISTS tenant_id UUID")
    op.execute(
        """
        UPDATE teams_meeting t
        SET tenant_id = s.tenant_id
        FROM note_taker_settings s
        WHERE t.tenant_id IS NULL
          AND t.note_taker_settings_system_name IS NOT NULL
          AND s.system_name = t.note_taker_settings_system_name
        """
    )
    op.execute(
        """
        ALTER TABLE teams_meeting
            ADD CONSTRAINT fk_teams_meeting_tenant_id
            FOREIGN KEY (tenant_id) REFERENCES tenant (id) ON DELETE CASCADE
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_teams_meeting_tenant_id "
        "ON teams_meeting (tenant_id)"
    )
    _enable_rls("teams_meeting")
    _attach_policy("teams_meeting", _NULLABLE_USING)

    # ── teams_user (NULLABLE via aad_object_id → user_account_oauth) ───
    op.execute("ALTER TABLE teams_user ADD COLUMN IF NOT EXISTS tenant_id UUID")
    op.execute(
        """
        UPDATE teams_user t
        SET tenant_id = u.tenant_id
        FROM user_account u
        JOIN user_account_oauth o ON o.user_id = u.id
        WHERE t.tenant_id IS NULL
          AND t.aad_object_id IS NOT NULL
          AND o.account_id = t.aad_object_id
        """
    )
    op.execute(
        """
        ALTER TABLE teams_user
            ADD CONSTRAINT fk_teams_user_tenant_id
            FOREIGN KEY (tenant_id) REFERENCES tenant (id) ON DELETE CASCADE
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_teams_user_tenant_id ON teams_user (tenant_id)"
    )
    _enable_rls("teams_user")
    _attach_policy("teams_user", _NULLABLE_USING)

    # ── teams_webhook_event (NULLABLE via parent teams_meeting) ────────
    op.execute(
        "ALTER TABLE teams_webhook_event ADD COLUMN IF NOT EXISTS tenant_id UUID"
    )
    op.execute(
        """
        UPDATE teams_webhook_event w
        SET tenant_id = m.tenant_id
        FROM teams_meeting m
        WHERE w.tenant_id IS NULL
          AND m.meeting_id IS NOT NULL
          AND m.meeting_id = w.resource_id
        """
    )
    op.execute(
        """
        ALTER TABLE teams_webhook_event
            ADD CONSTRAINT fk_teams_webhook_event_tenant_id
            FOREIGN KEY (tenant_id) REFERENCES tenant (id) ON DELETE CASCADE
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_teams_webhook_event_tenant_id "
        "ON teams_webhook_event (tenant_id)"
    )
    _enable_rls("teams_webhook_event")
    _attach_policy("teams_webhook_event", _NULLABLE_USING)


def schema_downgrades() -> None:
    for table in (
        "teams_webhook_event",
        "teams_user",
        "teams_meeting",
        "slack_oauth_states",
        "slack_installations",
    ):
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table}")
        _disable_rls(table)
        op.execute(f"DROP INDEX IF EXISTS ix_{table}_tenant_id")
        op.execute(
            f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS fk_{table}_tenant_id"
        )
        op.execute(f"ALTER TABLE {table} DROP COLUMN IF EXISTS tenant_id")
