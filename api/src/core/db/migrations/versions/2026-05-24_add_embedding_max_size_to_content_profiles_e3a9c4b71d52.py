# type: ignore
"""Simplify content profile indexing config.

Data-only migration. Iterates over all knowledge_graphs rows and updates each
content profile's ``chunker.options`` to:

  - Add ``embedding_max_size`` if missing. Backfill rule:
      * if ``embedding_max_size`` is already present, keep it;
      * else copy from the legacy ``chunk_max_size`` value;
      * else fall back to 18000.
  - Strip the obsolete keys ``indexing_mode``, ``indexing_overflow_strategy``
    and ``indexing_part_size`` introduced earlier on this branch. The
    indexing layer now always splits content into parts of
    ``embedding_max_size`` characters when the chunk exceeds that size.

The legacy ``chunk_max_size`` key is preserved (it is still used as a
chunker setting for recursive / kreuzberg strategies).

Revision ID: e3a9c4b71d52
Revises: b8d3e6f9a2c7
Create Date: 2026-04-27 00:00:00.000000+00:00

"""

from __future__ import annotations

import json

import sqlalchemy as sa
from alembic import op

__all__ = [
    "downgrade",
    "upgrade",
    "schema_upgrades",
    "schema_downgrades",
    "data_upgrades",
    "data_downgrades",
]

# revision identifiers, used by Alembic.
revision = "e3a9c4b71d52"
down_revision = "b8d3e6f9a2c7"
branch_labels = None
depends_on = None

DEFAULT_EMBEDDING_MAX_SIZE = 18000

OBSOLETE_KEYS = (
    "indexing_mode",
    "indexing_overflow_strategy",
    "indexing_part_size",
)


def upgrade() -> None:
    schema_upgrades()
    data_upgrades()


def downgrade() -> None:
    data_downgrades()
    schema_downgrades()


def schema_upgrades() -> None:
    pass


def schema_downgrades() -> None:
    pass


def _coerce_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def data_upgrades() -> None:
    conn = op.get_bind()
    rows = conn.execute(
        sa.text("SELECT id, settings FROM knowledge_graphs WHERE settings IS NOT NULL")
    ).fetchall()

    for row_id, settings in rows:
        if not isinstance(settings, dict):
            continue

        chunking = settings.get("chunking")
        if not isinstance(chunking, dict):
            continue

        content_settings = chunking.get("content_settings")
        if not isinstance(content_settings, list):
            continue

        modified = False
        for profile in content_settings:
            if not isinstance(profile, dict):
                continue

            chunker = profile.get("chunker")
            if not isinstance(chunker, dict):
                continue

            options = chunker.setdefault("options", {})

            if "embedding_max_size" not in options:
                options["embedding_max_size"] = _coerce_int(
                    options.get("chunk_max_size"), DEFAULT_EMBEDDING_MAX_SIZE
                )
                modified = True

            for key in OBSOLETE_KEYS:
                if key in options:
                    del options[key]
                    modified = True

        if modified:
            conn.execute(
                sa.text(
                    "UPDATE knowledge_graphs SET settings = :settings WHERE id = :id"
                ),
                {"settings": json.dumps(settings), "id": row_id},
            )


def data_downgrades() -> None:
    conn = op.get_bind()
    rows = conn.execute(
        sa.text("SELECT id, settings FROM knowledge_graphs WHERE settings IS NOT NULL")
    ).fetchall()

    for row_id, settings in rows:
        if not isinstance(settings, dict):
            continue

        chunking = settings.get("chunking")
        if not isinstance(chunking, dict):
            continue

        content_settings = chunking.get("content_settings")
        if not isinstance(content_settings, list):
            continue

        modified = False
        for profile in content_settings:
            if not isinstance(profile, dict):
                continue

            chunker = profile.get("chunker")
            if not isinstance(chunker, dict):
                continue

            options = chunker.get("options")
            if not isinstance(options, dict):
                continue

            if "embedding_max_size" in options:
                del options["embedding_max_size"]
                modified = True

        if modified:
            conn.execute(
                sa.text(
                    "UPDATE knowledge_graphs SET settings = :settings WHERE id = :id"
                ),
                {"settings": json.dumps(settings), "id": row_id},
            )
