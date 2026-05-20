"""Pydantic schemas for the entity audit log endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class EntityAuditLogEntry(BaseModel):
    """Compact list-item shape — omits the (potentially large) snapshots."""

    id: UUID
    tenant_id: UUID
    entity_type: str
    entity_id: UUID
    action: str
    actor_id: Optional[UUID] = None
    actor_type: str
    actor_display: str = ""
    source: str
    request_id: Optional[str] = None
    ai_request_id: Optional[UUID] = None
    can_restore: bool = False
    diff: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class EntityAuditLogDetail(EntityAuditLogEntry):
    """Full shape with both snapshots — used for the detail endpoint."""

    snapshot_before: Optional[dict[str, Any]] = None
    snapshot_after: Optional[dict[str, Any]] = None


class EntityAuditRestoreResponse(BaseModel):
    """Result of a restore call: the new state + the audit row that recorded it."""

    entity_type: str
    entity_id: UUID
    restored_from_audit_id: UUID
    restore_audit_id: Optional[UUID] = None
    snapshot_applied: dict[str, Any]
    can_restore: bool = False
