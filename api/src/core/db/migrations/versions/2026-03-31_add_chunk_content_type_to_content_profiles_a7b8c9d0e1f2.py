# type: ignore
"""Add chunk_content_type to content profile chunker options.

Data-only migration: iterates over all knowledge_graphs rows and adds
`chunk_content_type` to each content profile's `chunker.options` based
on the profile's reader name.

Mapping:
  - kreuzberg              -> "markdown"
  - sharepoint_page        -> "html"
  - fluid_topics_structured_documents -> "html"
  - all others             -> "plain_text"

Revision ID: a7b8c9d0e1f2
Revises: 5d27c945385a
Create Date: 2026-03-31 00:00:00.000000+00:00

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
revision = "a7b8c9d0e1f2"
down_revision = "5d27c945385a"
branch_labels = None
depends_on = None

READER_TO_CONTENT_TYPE = {
    "kreuzberg": "markdown",
    "sharepoint_page": "html",
    "fluid_topics_structured_documents": "html",
}
DEFAULT_CONTENT_TYPE = "plain_text"


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
            if "chunk_content_type" in options:
                continue

            reader = profile.get("reader", {})
            reader_name = reader.get("name", "") if isinstance(reader, dict) else ""
            options["chunk_content_type"] = READER_TO_CONTENT_TYPE.get(
                reader_name, DEFAULT_CONTENT_TYPE
            )
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

            if "chunk_content_type" in options:
                del options["chunk_content_type"]
                modified = True

        if modified:
            conn.execute(
                sa.text(
                    "UPDATE knowledge_graphs SET settings = :settings WHERE id = :id"
                ),
                {"settings": json.dumps(settings), "id": row_id},
            )
