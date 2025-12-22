# type: ignore
"""fix missing teams_meeting_id_seq for teams_meeting table

Revision ID: 9a82c5c1f8f3
Revises: 4d2f6f2f4f1a
Create Date: 2025-12-17 00:00:00.000000+00:00

"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

from alembic import op

if TYPE_CHECKING:
    pass

__all__ = [
    "downgrade",
    "upgrade",
    "schema_upgrades",
    "schema_downgrades",
    "data_upgrades",
    "data_downgrades",
]


# revision identifiers, used by Alembic.
revision = "9a82c5c1f8f3"
down_revision = "4d2f6f2f4f1a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        with op.get_context().autocommit_block():
            schema_upgrades()
            data_upgrades()


def downgrade() -> None:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        with op.get_context().autocommit_block():
            data_downgrades()
            schema_downgrades()


def schema_upgrades() -> None:
    """schema upgrade migrations go here."""
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
                    -- seed at 1 when table is empty; otherwise seed at max(id) and mark as called
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


def schema_downgrades() -> None:
    """schema downgrade migrations go here."""
    # no-op: keep sequence in place to avoid breaking existing ids


def data_upgrades() -> None:
    """Add any optional data upgrade migrations here!"""


def data_downgrades() -> None:
    """Add any optional data downgrade migrations here!"""
