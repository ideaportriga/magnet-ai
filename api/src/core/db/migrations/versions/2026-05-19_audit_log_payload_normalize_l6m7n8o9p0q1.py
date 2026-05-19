# type: ignore
"""Normalize legacy access_audit_log.payload rows.

Rows written before ``core.db.engine_factory._jsonb_encoder`` became
idempotent ended up stored as JSON-string scalars rather than JSONB
objects (a dict was serialized once by SQLAlchemy's engine-level
``json_serializer`` and then a second time by asyncpg's JSONB codec, so
PostgreSQL persisted ``'"{\\"email\\":...}"'`` instead of ``'{"email":...}'``).

On read those rows round-trip as Python ``str`` and fail the response
schema (``AccessAuditLogEntry.payload: dict[str, Any]``), which produced
HTTP 500 on every GET ``/api/admin/access-log`` — the admin Access Log
table appeared empty even for superusers.

This migration unwraps the JSON-string layer in place:

  UPDATE access_audit_log
  SET payload = (payload #>> '{}')::jsonb
  WHERE jsonb_typeof(payload) = 'string'
    AND (payload #>> '{}') ~ '^\\s*[\\{\\[]'

The regex guard skips strings whose content isn't a JSON object/array
(those would raise ``invalid input syntax for type json`` on the cast).
Such rows stay as-is and the read endpoint's ``_normalize_payload``
helper wraps them under ``_raw`` so a single unparseable row never hides
the rest of the trail. Re-running the migration is safe — once the
typeof is ``'object'`` the predicate excludes the row.

Revision ID: l6m7n8o9p0q1
Revises: k5l6m7n8o9p0
Create Date: 2026-05-19 16:00:00.000000+00:00
"""

from __future__ import annotations

import warnings

from alembic import op

__all__ = ["downgrade", "upgrade", "schema_upgrades", "schema_downgrades"]

revision = "l6m7n8o9p0q1"
down_revision = "k5l6m7n8o9p0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        with op.get_context().autocommit_block():
            schema_upgrades()


def downgrade() -> None:
    # The legacy storage shape was a bug; no schema change to revert.
    # Doing the inverse cast (object → JSON-string) would re-introduce
    # the very HTTP 500 this migration fixes, so the downgrade is a
    # no-op intentionally.
    pass


def schema_upgrades() -> None:
    op.execute(
        r"""
        UPDATE access_audit_log
        SET payload = (payload #>> '{}')::jsonb
        WHERE jsonb_typeof(payload) = 'string'
          AND (payload #>> '{}') ~ '^\s*[\{\[]'
        """
    )


def schema_downgrades() -> None:
    pass
