"""Controller for the entity audit log: history listing + restore.

Tenant-scoped by `Auth.tenant_id`; read endpoints require
``AUDIT_READ``, restore requires ``AUDIT_RESTORE``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from litestar import Controller, Request, get, post
from litestar.exceptions import (
    NotFoundException,
    PermissionDeniedException,
    ValidationException,
)
from sqlalchemy import select

from core.config.app import alchemy
from core.db.models.entity_audit_log import EntityAuditLog
from guards.permissions import Permission, require_permission
from middlewares.auth import Auth

from .schemas import (
    EntityAuditLogDetail,
    EntityAuditLogEntry,
    EntityAuditRestoreResponse,
)
from .service import (
    RestoreError,
    _normalize_jsonb,
    get_detail,
    list_entries,
    restore_from_audit,
)


def _require_tenant_id(request: Request) -> UUID:
    auth: Auth | None = request.scope.get("auth")
    if auth is None or not auth.tenant_id:
        raise PermissionDeniedException("Tenant context required")
    return UUID(auth.tenant_id)


def _to_entry(row: EntityAuditLog) -> EntityAuditLogEntry:
    return EntityAuditLogEntry(
        id=row.id,
        tenant_id=row.tenant_id,
        entity_type=row.entity_type,
        entity_id=row.entity_id,
        action=row.action,
        actor_id=row.actor_id,
        actor_type=row.actor_type,
        actor_display=row.actor_display or "",
        source=row.source,
        request_id=row.request_id,
        diff=_normalize_jsonb(row.diff) or {},
        created_at=row.created_at,
    )


def _to_detail(row: EntityAuditLog) -> EntityAuditLogDetail:
    return EntityAuditLogDetail(
        id=row.id,
        tenant_id=row.tenant_id,
        entity_type=row.entity_type,
        entity_id=row.entity_id,
        action=row.action,
        actor_id=row.actor_id,
        actor_type=row.actor_type,
        actor_display=row.actor_display or "",
        source=row.source,
        request_id=row.request_id,
        diff=_normalize_jsonb(row.diff) or {},
        snapshot_before=_normalize_jsonb(row.snapshot_before),
        snapshot_after=_normalize_jsonb(row.snapshot_after),
        created_at=row.created_at,
    )


class EntityAuditLogController(Controller):
    path = "/audit/entity-trail"
    tags = ["Admin / Entity Audit Trail"]

    @get(
        summary="List entity audit-log entries",
        guards=[require_permission(Permission.AUDIT_READ)],
    )
    async def list_entries_endpoint(
        self,
        request: Request,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        actor_id: Optional[UUID] = None,
        action: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[EntityAuditLogEntry]:
        tenant_id = _require_tenant_id(request)
        limit = max(1, min(int(limit), 500))
        offset = max(0, int(offset))
        async with alchemy.get_session() as session:
            rows = await list_entries(
                session,
                tenant_id=tenant_id,
                entity_type=entity_type,
                entity_id=entity_id,
                actor_id=actor_id,
                action=action,
                date_from=date_from,
                date_to=date_to,
                limit=limit,
                offset=offset,
            )
        return [_to_entry(r) for r in rows]

    @get(
        "/{audit_id:uuid}",
        summary="Get one audit entry with full snapshots",
        guards=[require_permission(Permission.AUDIT_READ)],
    )
    async def get_entry_endpoint(
        self,
        request: Request,
        audit_id: UUID,
    ) -> EntityAuditLogDetail:
        tenant_id = _require_tenant_id(request)
        async with alchemy.get_session() as session:
            row = await get_detail(session, tenant_id=tenant_id, audit_id=audit_id)
        if row is None:
            raise NotFoundException("Audit entry not found")
        return _to_detail(row)

    @post(
        "/{audit_id:uuid}/restore",
        summary="Restore entity to the state recorded in this audit entry",
        guards=[require_permission(Permission.AUDIT_RESTORE)],
    )
    async def restore_endpoint(
        self,
        request: Request,
        audit_id: UUID,
    ) -> EntityAuditRestoreResponse:
        tenant_id = _require_tenant_id(request)
        async with alchemy.get_session() as session:
            row = await get_detail(session, tenant_id=tenant_id, audit_id=audit_id)
            if row is None:
                raise NotFoundException("Audit entry not found")
            try:
                _, snapshot_applied = await restore_from_audit(
                    session, audit_row=row, tenant_id=tenant_id
                )
            except RestoreError as e:
                raise ValidationException(str(e)) from e
            await session.commit()

            # Find the audit row produced by this restore so callers can
            # link to it. The listener writes it in the same flush; query
            # for the newest row for this entity (excluding the source we
            # just read).
            restore_row = (
                (
                    await session.execute(
                        select(EntityAuditLog)
                        .where(EntityAuditLog.tenant_id == tenant_id)
                        .where(EntityAuditLog.entity_type == row.entity_type)
                        .where(EntityAuditLog.entity_id == row.entity_id)
                        .where(EntityAuditLog.id != row.id)
                        .order_by(EntityAuditLog.created_at.desc())
                        .limit(1)
                    )
                )
                .scalars()
                .first()
            )

        return EntityAuditRestoreResponse(
            entity_type=row.entity_type,
            entity_id=row.entity_id,
            restored_from_audit_id=row.id,
            restore_audit_id=restore_row.id if restore_row is not None else None,
            snapshot_applied=snapshot_applied,
        )
