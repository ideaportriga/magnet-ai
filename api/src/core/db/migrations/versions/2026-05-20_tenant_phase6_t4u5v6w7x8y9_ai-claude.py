# type: ignore
"""Tenant-isolation Phase 6 — architectural decisions.

Implements the four architectural choices made on Q-1, Q-2, Q-3, Q-6 in
`docs/tenant-isolation-plan_ai-claude.md`:

  providers      — per-tenant (Q-1). FK refactor: unique constraint on
                   `system_name` becomes composite `(tenant_id, system_name)`,
                   and the FKs from `ai_models.provider_system_name` and
                   `collections.provider_system_name` are rebuilt as
                   composite `(tenant_id, provider_system_name)`.
  ai_models      — per-tenant (Q-1). Inherits tenant_id from its parent
                   `providers` row.
  oauth_client   — per-tenant (Q-2). MCP clients registered inside a
                   tenant.
  jobs           — nullable tenant_id (Q-3). System housekeeping rows
                   have NULL; user-initiated rows carry the tenant.
                   Policy: IS NULL OR match.
  prompt_queue_configs — per-tenant (Q-6). Existing rows backfilled to
                   the `default` tenant.

Backfill of pre-existing data:
  - All existing `providers`, `ai_models`, `oauth_client`,
    `prompt_queue_configs` rows are assigned to the `default` tenant.
    Same pattern as previous tenant-scoping migrations
    (`2026-05-15_agents_rls_*`).
  - `jobs.tenant_id` left NULL (system jobs).

Revision ID: t4u5v6w7x8y9
Revises: s3t4u5v6w7x8
Create Date: 2026-05-20 21:00:00.000000+00:00
"""

from __future__ import annotations

import warnings

from alembic import op

__all__ = ["downgrade", "upgrade", "schema_upgrades", "schema_downgrades"]

revision = "t4u5v6w7x8y9"
down_revision = "s3t4u5v6w7x8"
branch_labels = None
depends_on = None


DEFAULT_TENANT_SLUG = "default"


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


# ── providers / ai_models — per-tenant with composite-FK refactor ───────


def _upgrade_providers_and_ai_models() -> None:
    # 1. Drop child FKs that point at providers.system_name (single col).
    op.execute(
        "ALTER TABLE ai_models DROP CONSTRAINT IF EXISTS "
        "fk_ai_models_provider_system_name_providers"
    )
    op.execute(
        "ALTER TABLE collections DROP CONSTRAINT IF EXISTS "
        "fk_collections_provider_system_name_providers"
    )
    op.execute(
        "ALTER TABLE note_taker_settings DROP CONSTRAINT IF EXISTS "
        "fk_note_taker_settings_provider_system_name_providers"
    )

    # 2. Drop the global unique on providers.system_name (we'll replace it
    #    with a composite one per tenant).
    op.execute(
        "ALTER TABLE providers DROP CONSTRAINT IF EXISTS uq_providers_system_name"
    )

    # 3. Add tenant_id to providers (nullable, backfill, NOT NULL).
    op.execute("ALTER TABLE providers ADD COLUMN IF NOT EXISTS tenant_id UUID")
    op.execute(
        f"""
        UPDATE providers
        SET tenant_id = (SELECT id FROM tenant WHERE slug = '{DEFAULT_TENANT_SLUG}')
        WHERE tenant_id IS NULL
        """
    )
    # Refuse to proceed if any provider still has no tenant (would only
    # happen if the `default` tenant doesn't exist).
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM providers WHERE tenant_id IS NULL) THEN
                RAISE EXCEPTION 'providers.tenant_id backfill failed — default tenant missing?';
            END IF;
        END $$;
        """
    )
    op.execute("ALTER TABLE providers ALTER COLUMN tenant_id SET NOT NULL")
    # Idempotent: drop the FK if a previous (partial) run created it.
    # autocommit_block commits each statement, so a crash mid-migration
    # leaves the constraint behind while alembic_version is unchanged.
    op.execute("ALTER TABLE providers DROP CONSTRAINT IF EXISTS fk_providers_tenant_id")
    op.execute(
        """
        ALTER TABLE providers
            ADD CONSTRAINT fk_providers_tenant_id
            FOREIGN KEY (tenant_id) REFERENCES tenant (id) ON DELETE CASCADE
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_providers_tenant_id ON providers (tenant_id)"
    )

    # 4. Composite uniqueness on (tenant_id, system_name).
    op.execute(
        "ALTER TABLE providers "
        "DROP CONSTRAINT IF EXISTS uq_providers_tenant_system_name"
    )
    op.execute(
        "ALTER TABLE providers ADD CONSTRAINT uq_providers_tenant_system_name "
        "UNIQUE (tenant_id, system_name)"
    )

    # 5. Add tenant_id to ai_models + backfill from provider.
    op.execute("ALTER TABLE ai_models ADD COLUMN IF NOT EXISTS tenant_id UUID")
    op.execute(
        """
        UPDATE ai_models m
        SET tenant_id = p.tenant_id
        FROM providers p
        WHERE m.tenant_id IS NULL
          AND p.system_name = m.provider_system_name
        """
    )
    # Models without a resolvable provider row fall back to the default
    # tenant — preserves legacy data and survives the autocommit-gap race.
    op.execute(
        f"""
        UPDATE ai_models
        SET tenant_id = (SELECT id FROM tenant WHERE slug = '{DEFAULT_TENANT_SLUG}')
        WHERE tenant_id IS NULL
        """
    )
    op.execute("ALTER TABLE ai_models ALTER COLUMN tenant_id SET NOT NULL")
    op.execute("ALTER TABLE ai_models DROP CONSTRAINT IF EXISTS fk_ai_models_tenant_id")
    op.execute(
        """
        ALTER TABLE ai_models
            ADD CONSTRAINT fk_ai_models_tenant_id
            FOREIGN KEY (tenant_id) REFERENCES tenant (id) ON DELETE CASCADE
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_ai_models_tenant_id ON ai_models (tenant_id)"
    )

    # 6. Re-create composite FKs on the children (collections / note_taker_settings
    #    already have tenant_id; ai_models was given one above).
    op.execute(
        "ALTER TABLE ai_models "
        "DROP CONSTRAINT IF EXISTS fk_ai_models_provider_tenant_system_name"
    )
    op.execute(
        """
        ALTER TABLE ai_models
            ADD CONSTRAINT fk_ai_models_provider_tenant_system_name
            FOREIGN KEY (tenant_id, provider_system_name)
            REFERENCES providers (tenant_id, system_name)
            ON DELETE CASCADE
        """
    )
    op.execute(
        "ALTER TABLE collections "
        "DROP CONSTRAINT IF EXISTS fk_collections_provider_tenant_system_name"
    )
    op.execute(
        """
        ALTER TABLE collections
            ADD CONSTRAINT fk_collections_provider_tenant_system_name
            FOREIGN KEY (tenant_id, provider_system_name)
            REFERENCES providers (tenant_id, system_name)
            ON DELETE CASCADE
        """
    )
    # note_taker_settings keeps the original "set NULL when provider goes
    # away" semantics. Column-specific SET NULL (PG 15+) nulls only
    # provider_system_name — note_taker_settings.tenant_id is NOT NULL and
    # must not be touched.
    op.execute(
        "ALTER TABLE note_taker_settings "
        "DROP CONSTRAINT IF EXISTS fk_note_taker_settings_provider_tenant_system_name"
    )
    op.execute(
        """
        ALTER TABLE note_taker_settings
            ADD CONSTRAINT fk_note_taker_settings_provider_tenant_system_name
            FOREIGN KEY (tenant_id, provider_system_name)
            REFERENCES providers (tenant_id, system_name)
            ON DELETE SET NULL (provider_system_name)
        """
    )

    # 7. RLS on providers and ai_models.
    _enable_rls("providers")
    _attach_policy("providers", _STANDARD_USING)
    _enable_rls("ai_models")
    _attach_policy("ai_models", _STANDARD_USING)


def _downgrade_providers_and_ai_models() -> None:
    def _attach_policy_drop(t: str) -> None:
        op.execute(f"DROP POLICY IF EXISTS {t}_tenant_isolation ON {t}")

    _attach_policy_drop("ai_models")
    _disable_rls("ai_models")
    _attach_policy_drop("providers")
    _disable_rls("providers")

    op.execute(
        "ALTER TABLE note_taker_settings DROP CONSTRAINT IF EXISTS "
        "fk_note_taker_settings_provider_tenant_system_name"
    )
    op.execute(
        "ALTER TABLE collections DROP CONSTRAINT IF EXISTS "
        "fk_collections_provider_tenant_system_name"
    )
    op.execute(
        "ALTER TABLE ai_models DROP CONSTRAINT IF EXISTS "
        "fk_ai_models_provider_tenant_system_name"
    )

    op.execute("DROP INDEX IF EXISTS ix_ai_models_tenant_id")
    op.execute("ALTER TABLE ai_models DROP CONSTRAINT IF EXISTS fk_ai_models_tenant_id")
    op.execute("ALTER TABLE ai_models DROP COLUMN IF EXISTS tenant_id")

    op.execute(
        "ALTER TABLE providers DROP CONSTRAINT IF EXISTS uq_providers_tenant_system_name"
    )
    op.execute("DROP INDEX IF EXISTS ix_providers_tenant_id")
    op.execute("ALTER TABLE providers DROP CONSTRAINT IF EXISTS fk_providers_tenant_id")
    op.execute("ALTER TABLE providers DROP COLUMN IF EXISTS tenant_id")

    op.execute(
        "ALTER TABLE providers DROP CONSTRAINT IF EXISTS uq_providers_system_name"
    )
    op.execute(
        "ALTER TABLE providers ADD CONSTRAINT uq_providers_system_name UNIQUE (system_name)"
    )
    op.execute(
        "ALTER TABLE ai_models "
        "DROP CONSTRAINT IF EXISTS fk_ai_models_provider_system_name_providers"
    )
    op.execute(
        """
        ALTER TABLE ai_models
            ADD CONSTRAINT fk_ai_models_provider_system_name_providers
            FOREIGN KEY (provider_system_name) REFERENCES providers (system_name)
            ON DELETE CASCADE
        """
    )
    op.execute(
        "ALTER TABLE collections "
        "DROP CONSTRAINT IF EXISTS fk_collections_provider_system_name_providers"
    )
    op.execute(
        """
        ALTER TABLE collections
            ADD CONSTRAINT fk_collections_provider_system_name_providers
            FOREIGN KEY (provider_system_name) REFERENCES providers (system_name)
            ON DELETE CASCADE
        """
    )
    op.execute(
        "ALTER TABLE note_taker_settings "
        "DROP CONSTRAINT IF EXISTS fk_note_taker_settings_provider_system_name_providers"
    )
    op.execute(
        """
        ALTER TABLE note_taker_settings
            ADD CONSTRAINT fk_note_taker_settings_provider_system_name_providers
            FOREIGN KEY (provider_system_name) REFERENCES providers (system_name)
            ON DELETE SET NULL
        """
    )


# ── oauth_client / prompt_queue_configs — simple per-tenant ─────────────


def _upgrade_simple_per_tenant(table: str) -> None:
    op.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS tenant_id UUID")
    op.execute(
        f"""
        UPDATE {table}
        SET tenant_id = (SELECT id FROM tenant WHERE slug = '{DEFAULT_TENANT_SLUG}')
        WHERE tenant_id IS NULL
        """
    )
    op.execute(
        f"""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM {table} WHERE tenant_id IS NULL) THEN
                RAISE EXCEPTION '{table}.tenant_id backfill failed — default tenant missing?';
            END IF;
        END $$;
        """
    )
    op.execute(f"ALTER TABLE {table} ALTER COLUMN tenant_id SET NOT NULL")
    op.execute(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS fk_{table}_tenant_id")
    op.execute(
        f"""
        ALTER TABLE {table}
            ADD CONSTRAINT fk_{table}_tenant_id
            FOREIGN KEY (tenant_id) REFERENCES tenant (id) ON DELETE CASCADE
        """
    )
    op.execute(
        f"CREATE INDEX IF NOT EXISTS ix_{table}_tenant_id ON {table} (tenant_id)"
    )
    _enable_rls(table)
    _attach_policy(table, _STANDARD_USING)


def _downgrade_simple_per_tenant(table: str) -> None:
    op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table}")
    _disable_rls(table)
    op.execute(f"DROP INDEX IF EXISTS ix_{table}_tenant_id")
    op.execute(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS fk_{table}_tenant_id")
    op.execute(f"ALTER TABLE {table} DROP COLUMN IF EXISTS tenant_id")


# ── jobs — nullable tenant_id, system-row pattern ────────────────────────


def _upgrade_jobs() -> None:
    op.execute("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS tenant_id UUID")
    # No backfill — existing rows are presumed to be system jobs (NULL is OK).
    op.execute("ALTER TABLE jobs DROP CONSTRAINT IF EXISTS fk_jobs_tenant_id")
    op.execute(
        """
        ALTER TABLE jobs
            ADD CONSTRAINT fk_jobs_tenant_id
            FOREIGN KEY (tenant_id) REFERENCES tenant (id) ON DELETE CASCADE
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_jobs_tenant_id ON jobs (tenant_id)")
    _enable_rls("jobs")
    _attach_policy("jobs", _NULLABLE_USING)


def _downgrade_jobs() -> None:
    op.execute("DROP POLICY IF EXISTS jobs_tenant_isolation ON jobs")
    _disable_rls("jobs")
    op.execute("DROP INDEX IF EXISTS ix_jobs_tenant_id")
    op.execute("ALTER TABLE jobs DROP CONSTRAINT IF EXISTS fk_jobs_tenant_id")
    op.execute("ALTER TABLE jobs DROP COLUMN IF EXISTS tenant_id")


def schema_upgrades() -> None:
    _upgrade_providers_and_ai_models()
    _upgrade_simple_per_tenant("oauth_client")
    _upgrade_simple_per_tenant("prompt_queue_configs")
    _upgrade_jobs()


def schema_downgrades() -> None:
    _downgrade_jobs()
    _downgrade_simple_per_tenant("prompt_queue_configs")
    _downgrade_simple_per_tenant("oauth_client")
    _downgrade_providers_and_ai_models()
