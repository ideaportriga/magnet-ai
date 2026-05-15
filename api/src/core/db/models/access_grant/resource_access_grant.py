"""
ResourceAccessGrant — explicit per-record ACL entries.

A grant attaches one principal (user | group | department) to one resource
(referenced by `resource_type` + `resource_id`) with a coarse `access_level`
(read | write | admin). PR 8 of the access-control plan.

Capability ceiling: grants only narrow access; they cannot raise a principal
above their global RBAC capability. `PermissionService` enforces that.

`resource_id` is intentionally a plain UUID with no FK — grants can target
any tenant-scoped table without us having to add a polymorphic FK or per-
resource grant table. The `(resource_type, resource_id)` pair acts like a
discriminated reference.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from sqlalchemy import ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from core.db.models.user.user import User


# String constants — keep wire-format stable.
PRINCIPAL_USER = "user"
PRINCIPAL_GROUP = "group"
PRINCIPAL_DEPARTMENT = "department"

ACCESS_READ = "read"
ACCESS_WRITE = "write"
ACCESS_ADMIN = "admin"


class ResourceAccessGrant(UUIDv7AuditBase):
    """One row = one principal granted some level of access to one resource."""

    __tablename__ = "resource_access_grant"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "resource_type",
            "resource_id",
            "principal_type",
            "principal_id",
            name="uq_resource_access_grant",
        ),
        Index(
            "ix_resource_access_grant_lookup",
            "tenant_id",
            "resource_type",
            "resource_id",
        ),
        Index(
            "ix_resource_access_grant_principal",
            "tenant_id",
            "principal_type",
            "principal_id",
        ),
        {"comment": "Per-record ACL entries (PR 8 of access-control plan)"},
    )

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    resource_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Resource bucket: 'agents', 'collections', ...",
    )

    resource_id: Mapped[UUID] = mapped_column(
        nullable=False,
        comment="UUID of the granted resource. No FK — polymorphic.",
    )

    principal_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="'user' | 'group' | 'department'",
    )

    principal_id: Mapped[UUID] = mapped_column(
        nullable=False,
        comment="UUID of the principal (user/group/department)",
    )

    access_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="'read' | 'write' | 'admin' — bounded by global capability",
    )

    granted_by_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("user_account.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Who created the grant (NULL after grantor is deleted)",
    )

    granted_by: Mapped[Optional[User]] = relationship(lazy="noload")

    def __repr__(self) -> str:
        return (
            f"<ResourceAccessGrant(tenant={self.tenant_id}, "
            f"{self.resource_type}/{self.resource_id}, "
            f"{self.principal_type}={self.principal_id}, level={self.access_level})>"
        )
