# type: ignore
"""Migrate entity extraction settings: rename performance_optimizations to advanced_settings,
move schema_format and max_extraction_iterations into it.

Revision ID: a1b2c3d4e5f7
Revises: b9c8d7e6f5a4
Create Date: 2026-05-14 00:00:00.000000+00:00

"""

from __future__ import annotations

import json
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
revision = "a1b2c3d4e5f7"
down_revision = "b9c8d7e6f5a4"
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


def schema_downgrades() -> None:
    """schema downgrade migrations go here."""


def data_upgrades() -> None:
    """
    For each knowledge graph whose settings contain entity_extraction:
    - Move schema_format and max_extraction_iterations from extraction into advanced_settings
    - Rename performance_optimizations to advanced_settings
    """
    connection = op.get_bind()

    rows = connection.execute(
        sa.text("SELECT id, settings FROM knowledge_graphs WHERE settings IS NOT NULL")
    ).fetchall()

    for row in rows:
        graph_id = row[0]
        settings = row[1]

        if not isinstance(settings, dict):
            continue

        entity_extraction = settings.get("entity_extraction")
        if not isinstance(entity_extraction, dict):
            continue

        changed = False

        extraction = entity_extraction.get("extraction")
        if isinstance(extraction, dict):
            schema_format = extraction.pop("schema_format", None)
            max_iterations = extraction.pop("max_extraction_iterations", None)
            if schema_format is not None or max_iterations is not None:
                changed = True

            # Build or update advanced_settings
            perf_opt = entity_extraction.pop("performance_optimizations", None)
            perf_tuning = entity_extraction.get("advanced_settings")
            if not isinstance(perf_tuning, dict):
                perf_tuning = perf_opt if isinstance(perf_opt, dict) else {}
            elif isinstance(perf_opt, dict):
                # advanced_settings already exists, just drop performance_optimizations
                changed = True

            if schema_format is not None:
                perf_tuning.setdefault("schema_format", schema_format)
            if max_iterations is not None:
                perf_tuning.setdefault("max_extraction_iterations", max_iterations)

            entity_extraction["advanced_settings"] = perf_tuning
            changed = True
        elif "performance_optimizations" in entity_extraction:
            # No extraction block, but rename performance_optimizations if present
            entity_extraction["advanced_settings"] = entity_extraction.pop(
                "performance_optimizations"
            )
            changed = True

        if not changed:
            continue

        settings["entity_extraction"] = entity_extraction
        connection.execute(
            sa.text("UPDATE knowledge_graphs SET settings = :settings WHERE id = :id"),
            {"settings": json.dumps(settings), "id": graph_id},
        )


def data_downgrades() -> None:
    """
    Reverse: move schema_format and max_extraction_iterations back into extraction,
    rename advanced_settings back to performance_optimizations.
    """
    connection = op.get_bind()

    rows = connection.execute(
        sa.text("SELECT id, settings FROM knowledge_graphs WHERE settings IS NOT NULL")
    ).fetchall()

    for row in rows:
        graph_id = row[0]
        settings = row[1]

        if not isinstance(settings, dict):
            continue

        entity_extraction = settings.get("entity_extraction")
        if not isinstance(entity_extraction, dict):
            continue

        changed = False

        perf_tuning = entity_extraction.get("advanced_settings")
        if isinstance(perf_tuning, dict):
            schema_format = perf_tuning.pop("schema_format", None)
            max_iterations = perf_tuning.pop("max_extraction_iterations", None)

            extraction = entity_extraction.get("extraction")
            if isinstance(extraction, dict):
                if schema_format is not None:
                    extraction.setdefault("schema_format", schema_format)
                if max_iterations is not None:
                    extraction.setdefault("max_extraction_iterations", max_iterations)

            entity_extraction.pop("advanced_settings")
            entity_extraction["performance_optimizations"] = perf_tuning
            changed = True

        if not changed:
            continue

        settings["entity_extraction"] = entity_extraction
        connection.execute(
            sa.text("UPDATE knowledge_graphs SET settings = :settings WHERE id = :id"),
            {"settings": json.dumps(settings), "id": graph_id},
        )
