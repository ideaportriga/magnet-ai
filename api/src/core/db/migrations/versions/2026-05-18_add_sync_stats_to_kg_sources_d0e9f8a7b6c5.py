# type: ignore
"""Add last_sync_stats and sync_progress JSONB columns to knowledge_graph_sources.

Revision ID: d0e9f8a7b6c5
Revises: c9d8e7f6a5b4
Create Date: 2026-05-18 12:00:00.000000+00:00

Expose the full sync pipeline lifecycle on each source row:

- ``last_sync_stats`` (JSONB): snapshot of the most recent completed sync
  (counters, timestamps, duration, top failing documents). Persisted in
  ``_finalize`` so the UI can show the breakdown long after the run.
- ``sync_progress`` (JSONB): mutated during an in-flight sync (phase,
  processed/total, current document) so the UI can show live progress.
  Cleared on finalize.
"""

from __future__ import annotations

import warnings

import sqlalchemy as sa
from advanced_alchemy.types import (
    GUID,
    ORA_JSONB,
    DateTimeUTC,
    EncryptedString,
    EncryptedText,
)
from alembic import op
from sqlalchemy import Text  # noqa: F401
from sqlalchemy.dialects.postgresql import JSONB

__all__ = [
    "downgrade",
    "upgrade",
    "schema_upgrades",
    "schema_downgrades",
    "data_upgrades",
    "data_downgrades",
]

sa.GUID = GUID
sa.DateTimeUTC = DateTimeUTC
sa.ORA_JSONB = ORA_JSONB
sa.EncryptedString = EncryptedString
sa.EncryptedText = EncryptedText
sa.Text = Text


# revision identifiers, used by Alembic.
revision = "d0e9f8a7b6c5"
down_revision = "c9d8e7f6a5b4"
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
    op.add_column(
        "knowledge_graph_sources",
        sa.Column(
            "last_sync_stats",
            JSONB,
            nullable=True,
            comment="Snapshot of the most recent completed sync (counters, timings, errors)",
        ),
    )
    op.add_column(
        "knowledge_graph_sources",
        sa.Column(
            "sync_progress",
            JSONB,
            nullable=True,
            comment="Live progress for an in-flight sync (phase, processed/total)",
        ),
    )


def schema_downgrades() -> None:
    op.drop_column("knowledge_graph_sources", "sync_progress")
    op.drop_column("knowledge_graph_sources", "last_sync_stats")


def data_upgrades() -> None:
    """Add any optional data upgrade migrations here!"""


def data_downgrades() -> None:
    """Add any optional data downgrade migrations here!"""
