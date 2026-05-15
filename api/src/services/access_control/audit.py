"""Audit log writer.

Single helper used by every access-control mutation. Designed to be called
from within an existing session/transaction — the caller commits.
"""

from __future__ import annotations

from typing import Any, Mapping
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models.audit import AccessAuditLog


async def write_audit_log(
    session: AsyncSession,
    *,
    tenant_id: UUID | str,
    actor_id: UUID | str | None,
    action: str,
    target_type: str,
    target_id: UUID | str | None = None,
    payload: Mapping[str, Any] | None = None,
) -> AccessAuditLog:
    """Append one row to access_audit_log. Caller commits."""
    row = AccessAuditLog(
        tenant_id=_as_uuid(tenant_id),
        actor_id=_as_uuid(actor_id) if actor_id else None,
        action=action,
        target_type=target_type,
        target_id=_as_uuid(target_id) if target_id else None,
        payload=dict(payload or {}),
    )
    session.add(row)
    await session.flush()
    return row


def _as_uuid(value: UUID | str) -> UUID:
    return value if isinstance(value, UUID) else UUID(str(value))
