"""Service helpers for the entity audit-log endpoints.

* ``list_entries`` / ``get_detail`` are thin SQL wrappers that respect
  the caller's tenant.
* ``restore_from_audit`` is the interesting one: take an audit row's
  ``snapshot_before`` (or ``snapshot_after`` for a ``delete`` row),
  strip server-controlled fields, and apply it to the target entity.
  The mutation flows through the ORM, which means the audit listener
  picks it up and emits a NEW audit row recording the restore — we
  return its id so the caller can link to it.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.audit import EntityAuditDescriptor, get_descriptor
from core.audit.context import (
    AuditContext,
    AuditSource,
    current_audit_context,
    set_audit_context,
    reset_audit_context,
)
from core.db.models.entity_audit_log import EntityAuditLog

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Read helpers
# ---------------------------------------------------------------------------


def _normalize_jsonb(raw: Any) -> Any:
    """Tolerate legacy JSONB rows persisted as JSON-encoded strings."""
    if raw is None or isinstance(raw, (dict, list)):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return {"_raw": raw}
    return {"_raw": raw}


async def list_entries(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    entity_type: Optional[str] = None,
    entity_id: Optional[UUID] = None,
    actor_id: Optional[UUID] = None,
    action: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[EntityAuditLog]:
    stmt = (
        select(EntityAuditLog)
        .where(EntityAuditLog.tenant_id == tenant_id)
        .order_by(EntityAuditLog.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if entity_type:
        stmt = stmt.where(EntityAuditLog.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(EntityAuditLog.entity_id == entity_id)
    if actor_id:
        stmt = stmt.where(EntityAuditLog.actor_id == actor_id)
    if action:
        stmt = stmt.where(EntityAuditLog.action == action)
    if date_from:
        stmt = stmt.where(EntityAuditLog.created_at >= date_from)
    if date_to:
        stmt = stmt.where(EntityAuditLog.created_at <= date_to)

    rows = (await session.execute(stmt)).scalars().all()
    return list(rows)


async def get_detail(
    session: AsyncSession, *, tenant_id: UUID, audit_id: UUID
) -> EntityAuditLog | None:
    stmt = select(EntityAuditLog).where(
        EntityAuditLog.id == audit_id, EntityAuditLog.tenant_id == tenant_id
    )
    return (await session.execute(stmt)).scalar_one_or_none()


# ---------------------------------------------------------------------------
# Restore
# ---------------------------------------------------------------------------


class RestoreError(Exception):
    """Raised when a restore cannot be applied."""


def _pick_target_snapshot(row: EntityAuditLog) -> dict[str, Any]:
    """Return the snapshot we should restore to.

    * ``update`` → ``snapshot_before`` (the state right before the change)
    * ``delete`` → ``snapshot_before`` (the state right before the row was
      removed — we use ``snapshot_before`` for symmetry; for delete rows it
      equals the row's final state since there is no "after")
    * ``create`` → no meaningful "older state" exists (would mean re-deleting)
    * ``restore`` → ``snapshot_after`` (the state we restored to is what
      ``snapshot_after`` describes for a previous restore)
    """
    if row.action == "create":
        raise RestoreError("Cannot restore from a 'create' audit row")
    if row.action == "restore":
        snap = row.snapshot_after
    else:
        snap = row.snapshot_before
    if not isinstance(snap, dict) or not snap:
        raise RestoreError("Audit row has no snapshot to restore from")
    return snap


def _strip_forbidden(
    snapshot: dict[str, Any], descriptor: EntityAuditDescriptor
) -> dict[str, Any]:
    forbidden = descriptor.forbidden_fields
    return {k: v for k, v in snapshot.items() if k not in forbidden}


async def restore_from_audit(
    session: AsyncSession,
    *,
    audit_row: EntityAuditLog,
    tenant_id: UUID,
) -> tuple[Any, dict[str, Any]]:
    """Apply the snapshot from ``audit_row`` to the target entity.

    Returns ``(entity, snapshot_applied)``. The entity is the ORM object
    after the change (already flushed). The listener will write the
    corresponding ``update`` / ``create`` audit row in the same flush;
    callers that need the row's id can read it from a follow-up query
    keyed by ``entity_id`` + the "restore" source tag we set on the
    context override below.
    """
    descriptor = get_descriptor(audit_row.entity_type)
    if descriptor is None:
        raise RestoreError(
            f"Entity type '{audit_row.entity_type}' is not registered for restore"
        )

    snapshot = _pick_target_snapshot(audit_row)
    payload = _strip_forbidden(snapshot, descriptor)

    model = descriptor.model
    existing = await session.get(model, audit_row.entity_id)

    base_ctx = current_audit_context.get()
    restore_ctx = _restore_context(base_ctx, tenant_id)
    token = set_audit_context(restore_ctx)
    try:
        if existing is None:
            # Re-create with the original primary key. tenant_id was stripped
            # by `_strip_forbidden`; put it back from the audit row.
            entity = model(
                id=audit_row.entity_id,
                tenant_id=tenant_id,
                **payload,
            )
            session.add(entity)
        else:
            if getattr(existing, "tenant_id", None) != tenant_id:
                raise RestoreError("Audit row tenant mismatch for restore target")
            for key, value in payload.items():
                setattr(existing, key, value)
            entity = existing

        await session.flush()
    finally:
        reset_audit_context(token)

    return entity, payload


def _restore_context(base: AuditContext | None, tenant_id: UUID) -> AuditContext:
    """Build the audit context for the restore write.

    Inherits actor identity from the caller's context (so the audit row
    correctly attributes the restore to the user that clicked the button)
    but forces ``source`` to RESTORE so the listener emits action="restore".
    """
    if base is None:
        from core.audit.context import system_audit_context

        return system_audit_context(
            source=AuditSource.RESTORE, display="restore", tenant_id=tenant_id
        )
    return AuditContext(
        actor_type=base.actor_type,
        actor_id=base.actor_id,
        actor_display=base.actor_display,
        source=AuditSource.RESTORE,
        request_id=base.request_id,
        tenant_id=tenant_id,
    )
