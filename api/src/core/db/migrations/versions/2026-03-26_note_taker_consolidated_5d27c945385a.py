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

Revision ID: a1b2c3d4e5f6
Revises: c4d5e6f7a8b9
Create Date: 2026-03-26 00:00:00.000000+00:00

"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

import sqlalchemy as sa
from advanced_alchemy.types import GUID, DateTimeUTC
from alembic import op
from sqlalchemy import Text  # noqa: F401
from sqlalchemy.dialects import postgresql
import advanced_alchemy.types
import advanced_alchemy.types.datetime
import advanced_alchemy.types.json

if TYPE_CHECKING:
    pass

__all__ = [
    "downgrade",
    "upgrade",
    "schema_upgrades",
    "schema_downgrades",
]

sa.GUID = GUID
sa.DateTimeUTC = DateTimeUTC
sa.Text = Text


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
    op.create_table(
        "teams_user",
        sa.Column(
            "aad_object_id",
            sa.Text(),
            nullable=True,
            comment="AAD object id from activity.from.aad_object_id",
        ),
        sa.Column(
            "teams_user_id",
            sa.Text(),
            nullable=False,
            comment="Teams user id from activity.from.id",
        ),
        sa.Column(
            "user_principal_name",
            sa.Text(),
            nullable=True,
            comment="User principal name from roster lookup",
        ),
        sa.Column(
            "email",
            sa.Text(),
            nullable=True,
            comment="Email from roster lookup (may be null)",
        ),
        sa.Column(
            "display_name",
            sa.Text(),
            nullable=True,
            comment="Display name from the activity",
        ),
        sa.Column(
            "scope",
            sa.Text(),
            nullable=False,
            comment='Teams scope: "personal" | "groupChat" | "channel"',
        ),
        sa.Column(
            "conversation_id",
            sa.Text(),
            nullable=False,
            comment="Conversation id for proactive messages",
        ),
        sa.Column(
            "service_url",
            sa.Text(),
            nullable=False,
            comment="Channel service URL",
        ),
        sa.Column(
            "bot_id",
            sa.Text(),
            nullable=False,
            comment="Bot's Teams id (activity.recipient.id)",
        ),
        sa.Column(
            "conversation_reference",
            sa.JSON().with_variant(
                postgresql.JSONB(astext_type=sa.Text()), "postgresql"
            ),
            nullable=False,
            comment="Serialized conversation reference snapshot",
        ),
        sa.Column(
            "last_seen_at",
            advanced_alchemy.types.datetime.DateTimeUTC(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            comment="Updated on every message/install event",
        ),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            advanced_alchemy.types.datetime.DateTimeUTC(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            advanced_alchemy.types.datetime.DateTimeUTC(timezone=True),
            nullable=False,
        ),
        sa.Column("id", GUID, nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_teams_user")),
    )
    # Final indexes include bot_id (migration #2 updated these)
    op.create_index(
        "ix_teams_user_aad_scope",
        "teams_user",
        ["aad_object_id", "scope", "bot_id"],
        unique=True,
        postgresql_where=sa.text("aad_object_id IS NOT NULL"),
    )
    op.create_index(
        "ix_teams_user_teams_scope",
        "teams_user",
        ["teams_user_id", "scope", "bot_id"],
        unique=True,
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
    op.add_column(
        "teams_meeting",
        sa.Column(
            "meeting_id",
            sa.Text(),
            nullable=True,
            comment="Teams meeting id from channel data",
        ),
    )
    op.add_column(
        "teams_meeting",
        sa.Column(
            "bot_id",
            sa.Text(),
            nullable=True,
            comment="Bot app id installed in meeting",
        ),
    )
    op.add_column(
        "teams_meeting",
        sa.Column(
            "added_by_user_id",
            sa.Text(),
            nullable=True,
            comment="Teams user id of the user who added the bot",
        ),
    )
    op.add_column(
        "teams_meeting",
        sa.Column(
            "added_by_aad_object_id",
            sa.Text(),
            nullable=True,
            comment="AAD object id of the user who added the bot",
        ),
    )
    op.add_column(
        "teams_meeting",
        sa.Column(
            "added_by_display_name",
            sa.Text(),
            nullable=True,
            comment="Display name of the user who added the bot",
        ),
    )
    op.add_column(
        "teams_meeting",
        sa.Column(
            "added_to_meeting_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Timestamp when the bot was added to the meeting",
        ),
    )
    op.add_column(
        "teams_meeting",
        sa.Column(
            "account_id",
            sa.Text(),
            nullable=True,
            comment="Salesforce account id linked to this meeting",
        ),
    )
    op.add_column(
        "teams_meeting",
        sa.Column(
            "account_name",
            sa.Text(),
            nullable=True,
            comment="Salesforce account name linked to this meeting",
        ),
    )
    op.add_column(
        "teams_meeting",
        sa.Column(
            "note_taker_settings_system_name",
            sa.Text(),
            nullable=True,
            comment="Note taker settings system name associated with this meeting",
        ),
    )

    # ── 4. ALTER teams_meeting — replace unique constraints (include bot_id) ──
    op.drop_constraint(
        op.f("uq_teams_meeting_chat_id"), "teams_meeting", type_="unique"
    )
    op.drop_constraint(
        op.f("uq_teams_meeting_graph_online_meeting_id"),
        "teams_meeting",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_teams_meeting_chat_id_bot_id", "teams_meeting", ["chat_id", "bot_id"]
    )
    op.create_unique_constraint(
        "uq_teams_meeting_graph_online_meeting_id_bot_id",
        "teams_meeting",
        ["graph_online_meeting_id", "bot_id"],
    )

    # ── 5. ALTER teams_meeting — drop dead columns ────────────────────
    op.drop_column("teams_meeting", "sa_orm_sentinel")
    op.drop_column("teams_meeting", "last_recordings_check_at")
    op.drop_column("teams_meeting", "title")
    op.drop_column("teams_meeting", "join_url")

    # ── 6. Create note_taker_settings table ───────────────────────────
    op.create_table(
        "note_taker_settings",
        sa.Column("id", GUID, nullable=False),
        sa.Column(
            "config",
            sa.JSON()
            .with_variant(postgresql.JSONB(astext_type=sa.Text), "cockroachdb")
            .with_variant(advanced_alchemy.types.json.ORA_JSONB(), "oracle")
            .with_variant(postgresql.JSONB(astext_type=sa.Text), "postgresql"),
            nullable=True,
            comment="Settings in JSON format",
        ),
        sa.Column("name", sa.String(length=255), nullable=False, comment="Entity name"),
        sa.Column("description", sa.Text, nullable=True, comment="Entity description"),
        sa.Column(
            "system_name",
            sa.String(length=255),
            nullable=False,
            comment="System name of the entity",
        ),
        sa.Column(
            "category", sa.String(length=255), nullable=True, comment="Entity category"
        ),
        sa.Column(
            "created_by",
            sa.String(length=255),
            nullable=True,
            comment="User who created the entity",
        ),
        sa.Column(
            "updated_by",
            sa.String(length=255),
            nullable=True,
            comment="User who last updated the entity",
        ),
        sa.Column("sa_orm_sentinel", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            advanced_alchemy.types.datetime.DateTimeUTC(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            advanced_alchemy.types.datetime.DateTimeUTC(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "provider_system_name",
            sa.String(255),
            sa.ForeignKey("providers.system_name", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("superuser_id", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_note_taker_settings")),
        sa.UniqueConstraint(
            "system_name", name=op.f("uq_note_taker_settings_system_name")
        ),
    )
    op.create_index(
        op.f("ix_note_taker_settings_description"),
        "note_taker_settings",
        ["description"],
        unique=False,
    )
    op.create_index(
        op.f("ix_note_taker_settings_name"),
        "note_taker_settings",
        ["name"],
        unique=False,
    )
    op.create_index(
        "ix_note_taker_settings_provider_system_name",
        "note_taker_settings",
        ["provider_system_name"],
    )

    # ── 7. Transcriptions — add meeting context columns ───────────────
    op.add_column("transcriptions", sa.Column("meeting_id", sa.Text(), nullable=True))
    op.add_column("transcriptions", sa.Column("chat_id", sa.Text(), nullable=True))
    op.add_column("transcriptions", sa.Column("initiated_by", sa.Text(), nullable=True))
    op.create_index("ix_transcriptions_meeting_id", "transcriptions", ["meeting_id"])
    op.create_index(
        "ix_transcriptions_initiated_by", "transcriptions", ["initiated_by"]
    )

    # ── 8. Create note_taker_pending_confirmation table ───────────────
    #    Columns match exactly what save_pending() / load_pending() use.
    op.create_table(
        "note_taker_pending_confirmation",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=False),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("job_id", sa.Text(), nullable=False),
        sa.Column("chat_id", sa.Text(), nullable=True),
        sa.Column("bot_id", sa.Text(), nullable=True),
        sa.Column("full_text", sa.Text(), nullable=True),
        sa.Column("raw_speaker_mapping", postgresql.JSONB(), nullable=True),
        sa.Column("suggested_keyterms", postgresql.JSONB(), nullable=True),
        sa.Column("settings_system_name", sa.Text(), nullable=True),
        sa.Column("settings_snapshot", postgresql.JSONB(), nullable=True),
        sa.Column("meeting_context", postgresql.JSONB(), nullable=True),
        sa.Column("invited_people", postgresql.JSONB(), nullable=True),
        sa.Column("conversation_reference", postgresql.JSONB(), nullable=True),
        sa.Column("pipeline_id", sa.Text(), nullable=True),
        sa.Column("conversation_date", sa.Text(), nullable=True),
        sa.Column("conversation_time", sa.Text(), nullable=True),
        sa.Column("expires_at", DateTimeUTC(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            DateTimeUTC(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_ntpc_job_id", "note_taker_pending_confirmation", ["job_id"])
    op.create_index("ix_ntpc_chat_id", "note_taker_pending_confirmation", ["chat_id"])
    op.create_index(
        "ix_ntpc_expires_at", "note_taker_pending_confirmation", ["expires_at"]
    )

    # ── 9. Create note_taker_jobs table ───────────────────────────────
    op.create_table(
        "note_taker_jobs",
        sa.Column("id", GUID(length=16), primary_key=True),
        sa.Column(
            "settings_id",
            GUID(length=16),
            sa.ForeignKey("note_taker_settings.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("user_id", sa.Text(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("participants", postgresql.JSONB(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("result", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            DateTimeUTC(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            DateTimeUTC(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_note_taker_jobs_settings_id", "note_taker_jobs", ["settings_id"]
    )
    op.create_index("ix_note_taker_jobs_user_id", "note_taker_jobs", ["user_id"])
    op.create_index("ix_note_taker_jobs_status", "note_taker_jobs", ["status"])

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
    op.drop_index("ix_note_taker_jobs_status", table_name="note_taker_jobs")
    op.drop_index("ix_note_taker_jobs_user_id", table_name="note_taker_jobs")
    op.drop_index("ix_note_taker_jobs_settings_id", table_name="note_taker_jobs")
    op.drop_table("note_taker_jobs")

    # ── 8. Drop note_taker_pending_confirmation ───────────────────────
    op.drop_index("ix_ntpc_expires_at", table_name="note_taker_pending_confirmation")
    op.drop_index("ix_ntpc_chat_id", table_name="note_taker_pending_confirmation")
    op.drop_index("ix_ntpc_job_id", table_name="note_taker_pending_confirmation")
    op.drop_table("note_taker_pending_confirmation")

    # ── 7. Drop transcriptions columns ────────────────────────────────
    op.drop_index("ix_transcriptions_initiated_by", table_name="transcriptions")
    op.drop_index("ix_transcriptions_meeting_id", table_name="transcriptions")
    op.drop_column("transcriptions", "initiated_by")
    op.drop_column("transcriptions", "chat_id")
    op.drop_column("transcriptions", "meeting_id")

    # ── 6. Drop note_taker_settings ───────────────────────────────────
    op.drop_index(
        "ix_note_taker_settings_provider_system_name", table_name="note_taker_settings"
    )
    op.drop_index(op.f("ix_note_taker_settings_name"), table_name="note_taker_settings")
    op.drop_index(
        op.f("ix_note_taker_settings_description"), table_name="note_taker_settings"
    )
    op.drop_table("note_taker_settings")

    # ── 5. Restore dead columns on teams_meeting ──────────────────────
    op.add_column(
        "teams_meeting",
        sa.Column(
            "join_url",
            sa.TEXT(),
            autoincrement=False,
            nullable=True,
            comment="Meeting join link",
        ),
    )
    op.add_column(
        "teams_meeting",
        sa.Column(
            "title",
            sa.TEXT(),
            autoincrement=False,
            nullable=True,
            comment="Meeting subject/title",
        ),
    )
    op.add_column(
        "teams_meeting",
        sa.Column(
            "last_recordings_check_at",
            postgresql.TIMESTAMP(timezone=True),
            autoincrement=False,
            nullable=True,
            comment="Last time recordings were checked for this meeting",
        ),
    )
    op.add_column(
        "teams_meeting",
        sa.Column("sa_orm_sentinel", sa.INTEGER(), autoincrement=False, nullable=True),
    )

    # ── 4. Restore original unique constraints ────────────────────────
    op.drop_constraint(
        "uq_teams_meeting_graph_online_meeting_id_bot_id",
        "teams_meeting",
        type_="unique",
    )
    op.drop_constraint(
        "uq_teams_meeting_chat_id_bot_id", "teams_meeting", type_="unique"
    )
    op.create_unique_constraint(
        op.f("uq_teams_meeting_graph_online_meeting_id"),
        "teams_meeting",
        ["graph_online_meeting_id"],
    )
    op.create_unique_constraint(
        op.f("uq_teams_meeting_chat_id"),
        "teams_meeting",
        ["chat_id"],
    )

    # ── 3. Drop added columns from teams_meeting ─────────────────────
    op.drop_column("teams_meeting", "note_taker_settings_system_name")
    op.drop_column("teams_meeting", "account_name")
    op.drop_column("teams_meeting", "account_id")
    op.drop_column("teams_meeting", "added_to_meeting_at")
    op.drop_column("teams_meeting", "added_by_display_name")
    op.drop_column("teams_meeting", "added_by_aad_object_id")
    op.drop_column("teams_meeting", "added_by_user_id")
    op.drop_column("teams_meeting", "bot_id")
    op.drop_column("teams_meeting", "meeting_id")

    # ── 2. Sequence stays (no-op, same as original) ───────────────────

    # ── 1. Drop teams_user ────────────────────────────────────────────
    op.drop_index("ix_teams_user_teams_scope", table_name="teams_user")
    op.drop_index("ix_teams_user_aad_scope", table_name="teams_user")
    op.drop_table("teams_user")
