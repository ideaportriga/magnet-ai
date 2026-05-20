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
    HTTPException,
    NotFoundException,
    PermissionDeniedException,
    ValidationException,
)
from litestar.status_codes import HTTP_403_FORBIDDEN
from sqlalchemy import select

from core.config.app import alchemy
from core.db.models.entity_audit_log import EntityAuditLog
from guards.permissions import Permission, get_effective_permissions, require_permission
from middlewares.auth import Auth
from services.access_control.permissions import PermissionService

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


def _to_entry(row: EntityAuditLog, *, can_restore: bool = False) -> EntityAuditLogEntry:
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
        ai_request_id=row.ai_request_id,
        can_restore=can_restore,
        diff=_normalize_jsonb(row.diff) or {},
        created_at=row.created_at,
    )


def _to_detail(
    row: EntityAuditLog, *, can_restore: bool = False
) -> EntityAuditLogDetail:
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
        ai_request_id=row.ai_request_id,
        can_restore=can_restore,
        diff=_normalize_jsonb(row.diff) or {},
        snapshot_before=_normalize_jsonb(row.snapshot_before),
        snapshot_after=_normalize_jsonb(row.snapshot_after),
        created_at=row.created_at,
    )


async def _can_access_audit_row(
    session,
    *,
    request: Request,
    row: EntityAuditLog,
    action: str = "view",
) -> bool:
    auth: Auth | None = request.scope.get("auth")
    if auth is None:
        return True
    from core.audit import get_descriptor

    descriptor = get_descriptor(row.entity_type)
    if descriptor is None:
        return False
    resource = await session.get(descriptor.model, row.entity_id)
    if resource is None:
        return action == "view" and row.action == "delete"
    return await PermissionService.can(
        session,
        auth=auth,
        action=action,
        resource_type=descriptor.resource_type,
        resource=resource,
    )


async def _can_restore_audit_row(
    session,
    *,
    request: Request,
    row: EntityAuditLog,
) -> bool:
    if row.action == "create":
        return False
    auth: Auth | None = request.scope.get("auth")
    effective = get_effective_permissions(auth)
    if Permission.AUDIT_RESTORE.value not in effective:
        return False
    from core.audit import get_descriptor

    descriptor = get_descriptor(row.entity_type)
    if descriptor is None or descriptor.write_permission.value not in effective:
        return False
    return await _can_access_audit_row(session, request=request, row=row, action="edit")


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
            allowed_rows = []
            for row in rows:
                if await _can_access_audit_row(session, request=request, row=row):
                    allowed_rows.append(
                        (
                            row,
                            await _can_restore_audit_row(
                                session, request=request, row=row
                            ),
                        )
                    )
        return [
            _to_entry(r, can_restore=can_restore) for r, can_restore in allowed_rows
        ]

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
            if row is not None and not await _can_access_audit_row(
                session, request=request, row=row
            ):
                row = None
            can_restore = (
                await _can_restore_audit_row(session, request=request, row=row)
                if row is not None
                else False
            )
        if row is None:
            raise NotFoundException("Audit entry not found")
        return _to_detail(row, can_restore=can_restore)

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
            from core.audit import get_descriptor

            descriptor = get_descriptor(row.entity_type)
            if descriptor is None:
                raise ValidationException(
                    f"Entity type '{row.entity_type}' is not registered for restore"
                )
            if descriptor.write_permission.value not in get_effective_permissions(
                request.scope.get("auth")
            ):
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN,
                    detail=f"Missing {descriptor.write_permission.value} permission",
                )
            if not await _can_access_audit_row(
                session, request=request, row=row, action="edit"
            ):
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN,
                    detail="You don't have permission to restore this entity",
                )
            try:
                _, snapshot_applied = await restore_from_audit(
                    session, audit_row=row, tenant_id=tenant_id
                )
            except RestoreError as e:
                raise ValidationException(str(e)) from e
            await session.flush()

            # Link to the audit row emitted by the restore flush.
            restore_row = (
                (
                    await session.execute(
                        select(EntityAuditLog)
                        .where(EntityAuditLog.tenant_id == tenant_id)
                        .where(EntityAuditLog.entity_type == row.entity_type)
                        .where(EntityAuditLog.entity_id == row.entity_id)
                        .where(EntityAuditLog.id != row.id)
                        .where(EntityAuditLog.action == "restore")
                        .order_by(EntityAuditLog.created_at.desc())
                        .limit(1)
                    )
                )
                .scalars()
                .first()
            )
            await session.commit()

        return EntityAuditRestoreResponse(
            entity_type=row.entity_type,
            entity_id=row.entity_id,
            restored_from_audit_id=row.id,
            restore_audit_id=restore_row.id if restore_row is not None else None,
            snapshot_applied=snapshot_applied,
            can_restore=False,
        )
