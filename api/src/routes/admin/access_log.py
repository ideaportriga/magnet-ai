"""Read endpoint for access_audit_log (PR 5 of access-control plan)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from litestar import Controller, Request, get
from litestar.exceptions import PermissionDeniedException
from pydantic import BaseModel
from sqlalchemy import select

from core.config.app import alchemy
from core.db.models.audit import AccessAuditLog
from guards.permissions import Permission, require_permission
from middlewares.auth import Auth


class AccessAuditLogEntry(BaseModel):
    id: UUID
    tenant_id: UUID
    actor_id: Optional[UUID] = None
    action: str
    target_type: str
    target_id: Optional[UUID] = None
    payload: dict[str, Any]
    created_at: datetime


def _require_tenant_id(request: Request) -> UUID:
    auth: Auth | None = request.scope.get("auth")
    if auth is None or not auth.tenant_id:
        raise PermissionDeniedException("Tenant context required")
    return UUID(auth.tenant_id)


class AccessLogController(Controller):
    path = "/access-log"
    tags = ["Admin / Access Log"]
    guards = [require_permission(Permission.AUDIT_READ)]

    @get(summary="List audit-log entries for the caller's tenant")
    async def list_entries(
        self,
        request: Request,
        actor_id: Optional[UUID] = None,
        action: Optional[str] = None,
        target_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AccessAuditLogEntry]:
        tenant_id = _require_tenant_id(request)
        limit = max(1, min(int(limit), 500))
        offset = max(0, int(offset))

        async with alchemy.get_session() as session:
            stmt = (
                select(AccessAuditLog)
                .where(AccessAuditLog.tenant_id == tenant_id)
                .order_by(AccessAuditLog.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            if actor_id is not None:
                stmt = stmt.where(AccessAuditLog.actor_id == actor_id)
            if action:
                stmt = stmt.where(AccessAuditLog.action == action)
            if target_type:
                stmt = stmt.where(AccessAuditLog.target_type == target_type)

            rows = (await session.execute(stmt)).scalars().all()

        return [
            AccessAuditLogEntry(
                id=r.id,
                tenant_id=r.tenant_id,
                actor_id=r.actor_id,
                action=r.action,
                target_type=r.target_type,
                target_id=r.target_id,
                payload=r.payload or {},
                created_at=r.created_at,
            )
            for r in rows
        ]
