"""Read endpoint for access_audit_log (PR 5 of access-control plan)."""

from __future__ import annotations

import json
from datetime import datetime
from logging import getLogger
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

logger = getLogger(__name__)


def _normalize_payload(raw: Any) -> dict[str, Any]:
    """Make the JSONB payload safe for the response schema.

    Legacy rows (written before ``engine_factory._jsonb_encoder`` became
    idempotent) hold a JSON-stringified-dict instead of a JSONB object,
    because asyncpg's codec re-encoded an already-serialized string.
    On read they come back as ``str`` and break ``dict[str, Any]``
    validation, which used to crash the whole list with HTTP 500.

    Parse strings; pass dicts through; coerce anything else to an empty
    dict so a single bad row never hides the rest of the audit trail.
    """
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return {"_raw": raw}
        if isinstance(parsed, dict):
            return parsed
        return {"_raw": parsed}
    return {"_raw": raw}


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
                payload=_normalize_payload(r.payload),
                created_at=r.created_at,
            )
            for r in rows
        ]
