"""
Access audit log — records every write to access-control state.

Captures role CRUD, user-role assign/revoke, resource grants, etc. Tenant-
scoped — every entry belongs to one tenant and is visible only to admins of
that tenant (enforced at the controller / RLS layer).
"""

from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.types import JsonB
from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column


class AccessAuditLog(UUIDv7AuditBase):
    """One row per access-control mutation."""

    __tablename__ = "access_audit_log"
    __table_args__ = (
        Index(
            "ix_access_audit_log_tenant_created",
            "tenant_id",
            "created_at",
        ),
        Index(
            "ix_access_audit_log_tenant_actor_created",
            "tenant_id",
            "actor_id",
            "created_at",
        ),
        {"comment": "Audit trail for access-control changes (PR 5 of plan)"},
    )

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Tenant scope — every entry belongs to one tenant",
    )

    actor_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("user_account.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Who performed the action (NULL for system / unattributed)",
    )

    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Dot-namespaced verb, e.g. 'role.create', 'user.role.assign'",
    )

    target_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Resource bucket: role | user | resource_access_grant | ...",
    )

    target_id: Mapped[Optional[UUID]] = mapped_column(
        nullable=True,
        comment="Optional FK-like reference to the target (uuid only, no FK)",
    )

    payload: Mapped[dict[str, Any]] = mapped_column(
        JsonB,
        nullable=False,
        default=dict,
        comment="Action-specific details (before/after, related ids, etc.)",
    )

    def __repr__(self) -> str:
        return f"<AccessAuditLog(action='{self.action}', target='{self.target_type}')>"
