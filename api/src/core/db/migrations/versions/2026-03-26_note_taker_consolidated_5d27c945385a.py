# type: ignore
"""note_taker: consolidated migration (replaces 9 individual note-taker migrations)

Creates:
  - teams_user (proactive messaging user state)
  - note_taker_settings (per-bot configuration, inherits UUIDAuditSimpleBase)
  - note_taker_pending_confirmation (speaker-mapping confirmation with TTL)
  - note_taker_jobs (preview pipeline job tracking)

Alters:
  - teams_meeting: add meeting_id, bot_id, added_by_*, added_to_meeting_at,
        account_id, account_name, note_taker_settings_system_name;
        fix id sequence; replace unique constraints to include bot_id;
        drop dead columns (sa_orm_sentinel, title, join_url, last_recordings_check_at)
  - transcriptions: add meeting_id, chat_id, initiated_by
  - note_taker_settings: add provider_system_name (FK -> providers), superuser_id

Revision ID: 5d27c945385a
Revises: d1c085c0ba5b
Create Date: 2026-03-26 00:00:00.000000+00:00

All DDL uses IF NOT EXISTS / IF EXISTS guards so the migration is safe to run
even if some objects were already created by the older individual migrations.

"""

from __future__ import annotations

import warnings

from alembic import op

__all__ = [
    "downgrade",
    "upgrade",
    "schema_upgrades",
    "schema_downgrades",
]


# revision identifiers, used by Alembic.
revision = "5d27c945385a"
down_revision = "d1c085c0ba5b"
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
    # ── 1. Create teams_user table ────────────────────────────────────
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS teams_user (
            aad_object_id TEXT,
            teams_user_id TEXT NOT NULL,
            user_principal_name TEXT,
            email TEXT,
            display_name TEXT,
            scope TEXT NOT NULL,
            conversation_id TEXT NOT NULL,
            service_url TEXT NOT NULL,
            bot_id TEXT NOT NULL,
            conversation_reference JSONB NOT NULL,
            last_seen_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            sa_orm_sentinel INTEGER,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
            id UUID NOT NULL,
            CONSTRAINT pk_teams_user PRIMARY KEY (id)
        )
        """
    )
    # Final indexes include bot_id (migration #2 updated these)
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ix_teams_user_aad_scope
        ON teams_user (aad_object_id, scope, bot_id)
        WHERE aad_object_id IS NOT NULL
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ix_teams_user_teams_scope
        ON teams_user (teams_user_id, scope, bot_id)
        """
    )

    # ── 2. Fix teams_meeting id sequence ──────────────────────────────
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'teams_meeting'
            ) THEN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_class WHERE relkind = 'S' AND relname = 'teams_meeting_id_seq'
                ) THEN
                    CREATE SEQUENCE teams_meeting_id_seq;
                    PERFORM setval(
                        'teams_meeting_id_seq',
                        GREATEST(COALESCE((SELECT max(id) FROM teams_meeting), 0), 1),
                        COALESCE((SELECT max(id) FROM teams_meeting), 0) > 0
                    );
                    ALTER SEQUENCE teams_meeting_id_seq OWNED BY teams_meeting.id;
                END IF;

                ALTER TABLE teams_meeting
                    ALTER COLUMN id SET DEFAULT nextval('teams_meeting_id_seq');
            END IF;
        END$$;
        """
    )

    # ── 3. ALTER teams_meeting — add columns ──────────────────────────
    op.execute("ALTER TABLE teams_meeting ADD COLUMN IF NOT EXISTS meeting_id TEXT")
    op.execute("ALTER TABLE teams_meeting ADD COLUMN IF NOT EXISTS bot_id TEXT")
    op.execute(
        "ALTER TABLE teams_meeting ADD COLUMN IF NOT EXISTS added_by_user_id TEXT"
    )
    op.execute(
        "ALTER TABLE teams_meeting ADD COLUMN IF NOT EXISTS added_by_aad_object_id TEXT"
    )
    op.execute(
        "ALTER TABLE teams_meeting ADD COLUMN IF NOT EXISTS added_by_display_name TEXT"
    )
    op.execute(
        "ALTER TABLE teams_meeting ADD COLUMN IF NOT EXISTS added_to_meeting_at TIMESTAMP WITH TIME ZONE"
    )
    op.execute("ALTER TABLE teams_meeting ADD COLUMN IF NOT EXISTS account_id TEXT")
    op.execute("ALTER TABLE teams_meeting ADD COLUMN IF NOT EXISTS account_name TEXT")
    op.execute(
        "ALTER TABLE teams_meeting ADD COLUMN IF NOT EXISTS note_taker_settings_system_name TEXT"
    )

    # ── 4. ALTER teams_meeting — replace unique constraints (include bot_id) ──
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'uq_teams_meeting_chat_id'
            ) THEN
                ALTER TABLE teams_meeting DROP CONSTRAINT uq_teams_meeting_chat_id;
            END IF;
        END$$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'uq_teams_meeting_graph_online_meeting_id'
            ) THEN
                ALTER TABLE teams_meeting DROP CONSTRAINT uq_teams_meeting_graph_online_meeting_id;
            END IF;
        END$$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'uq_teams_meeting_chat_id_bot_id'
            ) THEN
                ALTER TABLE teams_meeting ADD CONSTRAINT uq_teams_meeting_chat_id_bot_id UNIQUE (chat_id, bot_id);
            END IF;
        END$$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'uq_teams_meeting_graph_online_meeting_id_bot_id'
            ) THEN
                ALTER TABLE teams_meeting ADD CONSTRAINT uq_teams_meeting_graph_online_meeting_id_bot_id UNIQUE (graph_online_meeting_id, bot_id);
            END IF;
        END$$;
        """
    )

    # ── 5. ALTER teams_meeting — drop dead columns ────────────────────
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'teams_meeting' AND column_name = 'sa_orm_sentinel'
            ) THEN
                ALTER TABLE teams_meeting DROP COLUMN sa_orm_sentinel;
            END IF;
        END$$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'teams_meeting' AND column_name = 'last_recordings_check_at'
            ) THEN
                ALTER TABLE teams_meeting DROP COLUMN last_recordings_check_at;
            END IF;
        END$$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'teams_meeting' AND column_name = 'title'
            ) THEN
                ALTER TABLE teams_meeting DROP COLUMN title;
            END IF;
        END$$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'teams_meeting' AND column_name = 'join_url'
            ) THEN
                ALTER TABLE teams_meeting DROP COLUMN join_url;
            END IF;
        END$$;
        """
    )

    # ── 6. Create note_taker_settings table ───────────────────────────
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS note_taker_settings (
            id UUID NOT NULL,
            config JSONB,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            system_name VARCHAR(255) NOT NULL,
            category VARCHAR(255),
            created_by VARCHAR(255),
            updated_by VARCHAR(255),
            sa_orm_sentinel INTEGER,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
            provider_system_name VARCHAR(255) REFERENCES providers(system_name) ON DELETE SET NULL,
            superuser_id TEXT,
            CONSTRAINT pk_note_taker_settings PRIMARY KEY (id),
            CONSTRAINT uq_note_taker_settings_system_name UNIQUE (system_name)
        )
        """
    )
    # Add columns that may be missing if the old settings table already existed
    op.execute(
        """
        ALTER TABLE note_taker_settings
            ADD COLUMN IF NOT EXISTS provider_system_name VARCHAR(255) REFERENCES providers(system_name) ON DELETE SET NULL,
            ADD COLUMN IF NOT EXISTS superuser_id TEXT
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_note_taker_settings_description ON note_taker_settings (description)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_note_taker_settings_name ON note_taker_settings (name)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_note_taker_settings_provider_system_name ON note_taker_settings (provider_system_name)"
    )

    # ── 7. Transcriptions — add meeting context columns ───────────────
    op.execute("ALTER TABLE transcriptions ADD COLUMN IF NOT EXISTS meeting_id TEXT")
    op.execute("ALTER TABLE transcriptions ADD COLUMN IF NOT EXISTS chat_id TEXT")
    op.execute("ALTER TABLE transcriptions ADD COLUMN IF NOT EXISTS initiated_by TEXT")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_transcriptions_meeting_id ON transcriptions (meeting_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_transcriptions_initiated_by ON transcriptions (initiated_by)"
    )

    # ── 8. Create note_taker_pending_confirmation table ───────────────
    #    Columns match exactly what save_pending() / load_pending() use.
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS note_taker_pending_confirmation (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            job_id TEXT NOT NULL,
            chat_id TEXT,
            bot_id TEXT,
            full_text TEXT,
            raw_speaker_mapping JSONB,
            suggested_keyterms JSONB,
            settings_system_name TEXT,
            settings_snapshot JSONB,
            meeting_context JSONB,
            invited_people JSONB,
            conversation_reference JSONB,
            pipeline_id TEXT,
            conversation_date TEXT,
            conversation_time TEXT,
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_ntpc_job_id ON note_taker_pending_confirmation (job_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_ntpc_chat_id ON note_taker_pending_confirmation (chat_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_ntpc_expires_at ON note_taker_pending_confirmation (expires_at)"
    )

    # ── 9. Create note_taker_jobs table ───────────────────────────────
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS note_taker_jobs (
            id UUID NOT NULL PRIMARY KEY,
            settings_id UUID REFERENCES note_taker_settings(id) ON DELETE SET NULL,
            user_id TEXT,
            source_url TEXT,
            participants JSONB,
            status VARCHAR(50) NOT NULL DEFAULT 'pending',
            result JSONB,
            sa_orm_sentinel INTEGER,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "ALTER TABLE note_taker_jobs ADD COLUMN IF NOT EXISTS sa_orm_sentinel INTEGER"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_note_taker_jobs_settings_id ON note_taker_jobs (settings_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_note_taker_jobs_user_id ON note_taker_jobs (user_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_note_taker_jobs_status ON note_taker_jobs (status)"
    )

    # ── 10. Add state JSONB column to knowledge_graphs if not exists ──
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'knowledge_graphs' AND column_name = 'state'
            ) THEN
                ALTER TABLE knowledge_graphs ADD COLUMN state jsonb;
            END IF;
        END$$;
        """
    )


def schema_downgrades() -> None:
    # ── 10. Remove state from knowledge_graphs ────────────────────────
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'knowledge_graphs' AND column_name = 'state'
            ) THEN
                ALTER TABLE knowledge_graphs DROP COLUMN state;
            END IF;
        END$$;
        """
    )

    # ── 9. Drop note_taker_jobs ───────────────────────────────────────
    op.execute("DROP INDEX IF EXISTS ix_note_taker_jobs_status")
    op.execute("DROP INDEX IF EXISTS ix_note_taker_jobs_user_id")
    op.execute("DROP INDEX IF EXISTS ix_note_taker_jobs_settings_id")
    op.execute("DROP TABLE IF EXISTS note_taker_jobs")

    # ── 8. Drop note_taker_pending_confirmation ───────────────────────
    op.execute("DROP INDEX IF EXISTS ix_ntpc_expires_at")
    op.execute("DROP INDEX IF EXISTS ix_ntpc_chat_id")
    op.execute("DROP INDEX IF EXISTS ix_ntpc_job_id")
    op.execute("DROP TABLE IF EXISTS note_taker_pending_confirmation")

    # ── 7. Drop transcriptions columns ────────────────────────────────
    op.execute("DROP INDEX IF EXISTS ix_transcriptions_initiated_by")
    op.execute("DROP INDEX IF EXISTS ix_transcriptions_meeting_id")
    op.execute("ALTER TABLE transcriptions DROP COLUMN IF EXISTS initiated_by")
    op.execute("ALTER TABLE transcriptions DROP COLUMN IF EXISTS chat_id")
    op.execute("ALTER TABLE transcriptions DROP COLUMN IF EXISTS meeting_id")

    # ── 6. Drop note_taker_settings ───────────────────────────────────
    op.execute("DROP INDEX IF EXISTS ix_note_taker_settings_provider_system_name")
    op.execute("DROP INDEX IF EXISTS ix_note_taker_settings_name")
    op.execute("DROP INDEX IF EXISTS ix_note_taker_settings_description")
    op.execute("DROP TABLE IF EXISTS note_taker_settings")

    # ── 5. Restore dead columns on teams_meeting ──────────────────────
    op.execute("ALTER TABLE teams_meeting ADD COLUMN IF NOT EXISTS join_url TEXT")
    op.execute("ALTER TABLE teams_meeting ADD COLUMN IF NOT EXISTS title TEXT")
    op.execute(
        "ALTER TABLE teams_meeting ADD COLUMN IF NOT EXISTS last_recordings_check_at TIMESTAMP WITH TIME ZONE"
    )
    op.execute(
        "ALTER TABLE teams_meeting ADD COLUMN IF NOT EXISTS sa_orm_sentinel INTEGER"
    )

    # ── 4. Restore original unique constraints ────────────────────────
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'uq_teams_meeting_graph_online_meeting_id_bot_id'
            ) THEN
                ALTER TABLE teams_meeting DROP CONSTRAINT uq_teams_meeting_graph_online_meeting_id_bot_id;
            END IF;
        END$$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'uq_teams_meeting_chat_id_bot_id'
            ) THEN
                ALTER TABLE teams_meeting DROP CONSTRAINT uq_teams_meeting_chat_id_bot_id;
            END IF;
        END$$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'uq_teams_meeting_graph_online_meeting_id'
            ) THEN
                ALTER TABLE teams_meeting ADD CONSTRAINT uq_teams_meeting_graph_online_meeting_id UNIQUE (graph_online_meeting_id);
            END IF;
        END$$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'uq_teams_meeting_chat_id'
            ) THEN
                ALTER TABLE teams_meeting ADD CONSTRAINT uq_teams_meeting_chat_id UNIQUE (chat_id);
            END IF;
        END$$;
        """
    )

    # ── 3. Drop added columns from teams_meeting ─────────────────────
    op.execute(
        "ALTER TABLE teams_meeting DROP COLUMN IF EXISTS note_taker_settings_system_name"
    )
    op.execute("ALTER TABLE teams_meeting DROP COLUMN IF EXISTS account_name")
    op.execute("ALTER TABLE teams_meeting DROP COLUMN IF EXISTS account_id")
    op.execute("ALTER TABLE teams_meeting DROP COLUMN IF EXISTS added_to_meeting_at")
    op.execute("ALTER TABLE teams_meeting DROP COLUMN IF EXISTS added_by_display_name")
    op.execute("ALTER TABLE teams_meeting DROP COLUMN IF EXISTS added_by_aad_object_id")
    op.execute("ALTER TABLE teams_meeting DROP COLUMN IF EXISTS added_by_user_id")
    op.execute("ALTER TABLE teams_meeting DROP COLUMN IF EXISTS bot_id")
    op.execute("ALTER TABLE teams_meeting DROP COLUMN IF EXISTS meeting_id")

    # ── 2. Sequence stays (no-op, same as original) ───────────────────

    # ── 1. Drop teams_user ────────────────────────────────────────────
    op.execute("DROP INDEX IF EXISTS ix_teams_user_teams_scope")
    op.execute("DROP INDEX IF EXISTS ix_teams_user_aad_scope")
    op.execute("DROP TABLE IF EXISTS teams_user")
