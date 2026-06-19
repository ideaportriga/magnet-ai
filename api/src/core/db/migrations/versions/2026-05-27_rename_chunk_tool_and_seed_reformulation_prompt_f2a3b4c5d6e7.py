# type: ignore
"""Rename KG chunk tool to retrieveChunks and seed the query-reformulation prompt.

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-05-27 00:00:00.000000+00:00

This migration:

- Renames the persisted KG retrieval tool key ``findChunksBySimilarity`` ->
  ``retrieveChunks`` inside ``knowledge_graphs.settings.retrieval_tools``,
  preserving all nested config values and adding the new ``promptTemplateName``
  field (defaulting to ``KG_CHUNK_QUERY_REFORMULATION``) when absent.
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


# revision identifiers, used by Alembic.
revision = "f2a3b4c5d6e7"
down_revision = "e1f2a3b4c5d6"
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
    """No schema changes."""


def schema_downgrades() -> None:
    """No schema changes."""


def data_upgrades() -> None:
    """Rename the tool key and seed the reformulation prompt."""
    conn = op.get_bind()

    # 1) Rename findChunksBySimilarity -> retrieveChunks, preserving nested config
    #    and adding promptTemplateName when it is missing. Object merge (||) is
    #    right-biased, so existing values win over the injected default.
    conn.execute(
        sa.text(
            """
            UPDATE knowledge_graphs
            SET settings = jsonb_set(
                settings,
                '{retrieval_tools}',
                ((settings->'retrieval_tools') - 'findChunksBySimilarity')
                || jsonb_build_object(
                    'retrieveChunks',
                    jsonb_build_object(
                        'promptTemplateName', 'KG_CHUNK_QUERY_REFORMULATION'
                    )
                    || (settings->'retrieval_tools'->'findChunksBySimilarity')
                )
            )
            WHERE settings IS NOT NULL
              AND (settings->'retrieval_tools'->'findChunksBySimilarity') IS NOT NULL
            """
        )
    )


def data_downgrades() -> None:
    """Reverse the tool key rename (drops the added promptTemplateName)."""
    conn = op.get_bind()

    conn.execute(
        sa.text(
            """
            UPDATE knowledge_graphs
            SET settings = jsonb_set(
                settings,
                '{retrieval_tools}',
                ((settings->'retrieval_tools') - 'retrieveChunks')
                || jsonb_build_object(
                    'findChunksBySimilarity',
                    ((settings->'retrieval_tools'->'retrieveChunks') - 'promptTemplateName')
                )
            )
            WHERE settings IS NOT NULL
              AND (settings->'retrieval_tools'->'retrieveChunks') IS NOT NULL
            """
        )
    )
