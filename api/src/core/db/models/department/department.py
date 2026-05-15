"""
Department — organizational unit inside a tenant (PR 8 of access-control plan).

Distinct from `user_group`: department represents an org-chart unit used by
`visibility='department'` on resources and by `is_lead` for elevated rights
within the unit. Groups are ad-hoc sharing buckets — see plan PR 8 design.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from core.db.models.tenant.tenant import Tenant


class Department(UUIDv7AuditBase):
    """A department within a tenant."""

    __tablename__ = "department"
    __table_args__ = (
        Index(
            "uq_department_slug_per_tenant",
            "tenant_id",
            "slug",
            unique=True,
        ),
        {"comment": "Departments — org-chart units inside a tenant"},
    )

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="URL-safe identifier (unique within tenant)",
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Display name",
    )

    parent_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("department.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Optional parent for nested org chart",
    )

    tenant: Mapped[Tenant] = relationship(lazy="noload")

    def __repr__(self) -> str:
        return f"<Department(slug='{self.slug}')>"
