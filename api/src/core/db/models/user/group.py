"""
Group table definition.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from core.db.models.tenant.tenant import Tenant


class Group(UUIDv7AuditBase):
    """Tenant-scoped group for ad-hoc sharing and grants.

    Slug and name are unique **within a tenant** — two tenants can each have
    a group called "Project X". Migration `e7f8a9b0c1d2` (PR 6) replaces the
    legacy global UNIQUE with partial indexes. SQLAlchemy `Index(...)`
    entries mirror those so `metadata.create_all` produces a matching schema
    for the test suite.
    """

    __tablename__ = "user_group"
    __table_args__ = (
        Index(
            "uq_user_group_slug_per_tenant",
            "tenant_id",
            "slug",
            unique=True,
        ),
        Index(
            "uq_user_group_name_per_tenant",
            "tenant_id",
            "name",
            unique=True,
        ),
        {"comment": "Tenant-scoped user groups for sharing and grants"},
    )

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Tenant scope — groups never cross tenant boundaries",
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Display name (unique within tenant)",
    )

    slug: Mapped[str] = mapped_column(
        String(255),
        index=True,
        nullable=False,
        comment="URL-safe identifier (unique within tenant)",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        default=None,
        comment="Group description",
    )

    tenant: Mapped[Tenant] = relationship(lazy="noload")

    def __repr__(self) -> str:
        return f"<Group(slug='{self.slug}')>"
