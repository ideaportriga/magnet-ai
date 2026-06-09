# type: ignore
"""Backfill hybrid-search tool config for existing KG retrieval tools.

Revision ID: a3b4c5d6e7f9
Revises: f2a3b4c5d6e7
Create Date: 2026-05-28 00:00:00.000000+00:00

Graphs created before hybrid search shipped have ``retrieveChunks`` /
``findDocumentsBySummarySimilarity`` tool configs that lack the fields the
retrievers now read directly (e.g. ``rrfK``, ``searchMethod``), which raises
``KeyError: 'rrfK'`` at retrieval time. This migration injects the default
hybrid-search fields into both tools, preserving any values already present
(left-biased merge: defaults are overridden by existing config).
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
revision = "a3b4c5d6e7f9"
down_revision = "f2a3b4c5d6e7"
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
    """Inject default hybrid-search fields into existing KG retrieval tools."""
    conn = op.get_bind()

    # findDocumentsBySummarySimilarity: searchMethod, scoreThreshold, limit, rrfK.
    # Defaults are merged first so any existing per-graph values win.
    conn.execute(
        sa.text(
            """
            UPDATE knowledge_graphs
            SET settings = jsonb_set(
                settings,
                '{retrieval_tools,findDocumentsBySummarySimilarity}',
                jsonb_build_object(
                    'searchMethod', 'hybrid',
                    'scoreThreshold', 0,
                    'limit', 5,
                    'rrfK', 60
                )
                || (settings->'retrieval_tools'->'findDocumentsBySummarySimilarity')
            )
            WHERE settings IS NOT NULL
              AND (settings->'retrieval_tools'->'findDocumentsBySummarySimilarity')
                  IS NOT NULL
            """
        )
    )

    # retrieveChunks: full hybrid config set used by the chunk retriever.
    conn.execute(
        sa.text(
            """
            UPDATE knowledge_graphs
            SET settings = jsonb_set(
                settings,
                '{retrieval_tools,retrieveChunks}',
                jsonb_build_object(
                    'searchMethod', 'hybrid',
                    'scoreThreshold', 0,
                    'limit', 5,
                    'rrfK', 60,
                    'candidatePoolSize', 30,
                    'keywordVariants', 1,
                    'vectorVariants', 1,
                    'promptTemplateName', 'KG_CHUNK_QUERY_REFORMULATION'
                )
                || (settings->'retrieval_tools'->'retrieveChunks')
            )
            WHERE settings IS NOT NULL
              AND (settings->'retrieval_tools'->'retrieveChunks') IS NOT NULL
            """
        )
    )


def data_downgrades() -> None:
    """No-op: the backfilled defaults are harmless and indistinguishable from
    values that may have been set intentionally, so we do not strip them."""
