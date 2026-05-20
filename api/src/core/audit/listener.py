"""SQLAlchemy event listener that emits ``entity_audit_log`` rows.

Hooks two events on every ``Session``:

* ``before_flush`` — capture the pending changes (new/dirty/deleted) and
  the *before* snapshots while attribute history is still attached.
* ``after_flush_postexec`` — by then the new rows have their PK assigned
  (UUIDv7 server-side default has run), so we can stamp ``entity_id`` and
  insert the audit rows in the same transaction.

Both flush events run inside the same transaction as the business write,
so audit and entity are committed atomically — a failed commit rolls back
both.

The listener silently no-ops when:
  * the session has no ``Auditable`` instances pending;
  * the listener was already installed (idempotent ``install_audit_listener``).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import event, inspect
from sqlalchemy.orm import Session

from .context import (
    AuditContext,
    AuditSource,
    current_audit_context,
    system_audit_context,
)
from .mixin import Auditable
from .snapshot import (
    compute_diff,
    snapshot_before_update,
    snapshot_current,
)

logger = logging.getLogger(__name__)

_LISTENER_INSTALLED = False
_SESSION_KEY = "__entity_audit_pending__"


@dataclass
class _PendingAudit:
    action: str  # "create" | "update" | "delete"
    entity_type: str
    obj: Auditable
    before: dict[str, Any] | None  # snapshot before the change


def _is_auditable(obj: Any) -> bool:
    if not isinstance(obj, Auditable):
        return False
    if not obj.__class__.__audit_entity_type__:
        logger.warning(
            "Auditable model %s is missing __audit_entity_type__; skipping",
            obj.__class__.__name__,
        )
        return False
    return True


def _resolve_tenant_id(obj: Auditable, ctx: AuditContext) -> UUID | None:
    """Pick the tenant for the audit row.

    Prefers the entity's own ``tenant_id`` (the most accurate — the row
    being audited belongs to that tenant). Falls back to the actor's
    tenant from the context (e.g. when deleting and the column is already
    gone from the in-memory state).
    """
    value = getattr(obj, "tenant_id", None)
    if value is not None:
        if isinstance(value, UUID):
            return value
        try:
            return UUID(str(value))
        except (TypeError, ValueError):
            pass
    if ctx.tenant_id is not None:
        return ctx.tenant_id
    return None


def _entity_pk(obj: Auditable) -> UUID | None:
    """Resolve the primary key as a UUID, post-flush if necessary."""
    state = inspect(obj)
    identity = state.identity
    if identity:
        pk = identity[0]
        if isinstance(pk, UUID):
            return pk
        try:
            return UUID(str(pk))
        except (TypeError, ValueError):
            return None
    raw = getattr(obj, "id", None)
    if isinstance(raw, UUID):
        return raw
    if raw is None:
        return None
    try:
        return UUID(str(raw))
    except (TypeError, ValueError):
        return None


def _build_audit_row(pending: _PendingAudit, ctx: AuditContext):
    # Lazy import to avoid a circular ``core.audit`` ↔ ``core.db.models``
    # import cycle at module-load time. Models pull config, config pulls
    # services, services pull domain controllers, controllers pull models
    # that re-import audit — only the runtime flush actually needs the
    # ORM class.
    from core.db.models.entity_audit_log import EntityAuditLog

    pk = _entity_pk(pending.obj)
    if pk is None:
        logger.warning(
            "Audit listener: %s on %s has no resolvable primary key; skipping row",
            pending.action,
            pending.entity_type,
        )
        return None

    if pending.action == "delete":
        snapshot_after: dict[str, Any] | None = None
    else:
        snapshot_after = snapshot_current(pending.obj)

    snapshot_before = pending.before
    diff = compute_diff(snapshot_before, snapshot_after)

    tenant_id = _resolve_tenant_id(pending.obj, ctx)
    if tenant_id is None:
        logger.warning(
            "Audit listener: %s on %s/%s has no tenant_id; skipping row",
            pending.action,
            pending.entity_type,
            pk,
        )
        return None

    action = "restore" if ctx.source == AuditSource.RESTORE else pending.action

    return EntityAuditLog(
        tenant_id=tenant_id,
        entity_type=pending.entity_type,
        entity_id=pk,
        action=action,
        actor_id=ctx.actor_id,
        actor_type=ctx.actor_type.value,
        actor_display=ctx.actor_display or "",
        source=ctx.source.value,
        request_id=ctx.request_id,
        snapshot_before=snapshot_before,
        snapshot_after=snapshot_after,
        diff=diff,
        ai_request_id=ctx.ai_request_id,
    )


def install_audit_listener() -> None:
    """Idempotent installer for the global session-level audit listener."""
    global _LISTENER_INSTALLED
    if _LISTENER_INSTALLED:
        return

    @event.listens_for(Session, "before_flush")
    def _capture_audit(session, flush_context, instances):  # noqa: ANN001
        pending: list[_PendingAudit] = []

        for obj in list(session.new):
            if not _is_auditable(obj):
                continue
            pending.append(
                _PendingAudit(
                    action="create",
                    entity_type=obj.__class__.__audit_entity_type__,
                    obj=obj,
                    before=None,
                )
            )

        for obj in list(session.dirty):
            if not _is_auditable(obj):
                continue
            if not session.is_modified(obj, include_collections=False):
                continue
            pending.append(
                _PendingAudit(
                    action="update",
                    entity_type=obj.__class__.__audit_entity_type__,
                    obj=obj,
                    before=snapshot_before_update(obj),
                )
            )

        for obj in list(session.deleted):
            if not _is_auditable(obj):
                continue
            pending.append(
                _PendingAudit(
                    action="delete",
                    entity_type=obj.__class__.__audit_entity_type__,
                    obj=obj,
                    before=snapshot_current(obj),
                )
            )

        if pending:
            session.info[_SESSION_KEY] = pending

    @event.listens_for(Session, "after_flush_postexec")
    def _emit_audit_rows(session, flush_context):  # noqa: ANN001
        pending = session.info.pop(_SESSION_KEY, None)
        if not pending:
            return

        ctx = current_audit_context.get() or system_audit_context()
        rows = []
        for entry in pending:
            row = _build_audit_row(entry, ctx)
            if row is not None:
                rows.append(row)

        if rows:
            session.add_all(rows)

    _LISTENER_INSTALLED = True


# Install at import time so any session created by either the Litestar
# alchemy plugin or the standalone ``async_session_maker`` is covered.
install_audit_listener()
