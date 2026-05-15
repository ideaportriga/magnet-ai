"""
Role table definition.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from core.db.models.tenant.tenant import Tenant

    from .role_permission import RolePermission


class Role(UUIDv7AuditBase):
    """Role for RBAC.

    Two flavours, distinguished by `is_system`:

    - **System role** (`is_system=true`, `tenant_id IS NULL`): seeded by
      migration, immutable. Slugs `admin`, `user`, `viewer` are globally
      unique among system roles.
    - **Custom tenant role** (`is_system=false`, `tenant_id IS NOT NULL`):
      created via admin UI in PR 5. Slug/name unique within its tenant.

    The CHECK constraint and partial unique indexes are owned by migration
    `c5d6e7f8a9b0` (Postgres-only). SQLAlchemy metadata reflects them so
    `metadata.create_all` (used by the test suite) sets up an equivalent
    schema.
    """

    __tablename__ = "role"
    __table_args__ = (
        # System: tenant_id IS NULL ↔ is_system = TRUE
        CheckConstraint(
            "(is_system = TRUE AND tenant_id IS NULL) OR "
            "(is_system = FALSE AND tenant_id IS NOT NULL)",
            name="ck_role_system_invariant",
        ),
        Index(
            "uq_role_slug_system",
            "slug",
            unique=True,
            postgresql_where="tenant_id IS NULL",
        ),
        Index(
            "uq_role_name_system",
            "name",
            unique=True,
            postgresql_where="tenant_id IS NULL",
        ),
        Index(
            "uq_role_slug_per_tenant",
            "tenant_id",
            "slug",
            unique=True,
            postgresql_where="tenant_id IS NOT NULL",
        ),
        Index(
            "uq_role_name_per_tenant",
            "tenant_id",
            "name",
            unique=True,
            postgresql_where="tenant_id IS NOT NULL",
        ),
        {"comment": "Roles for role-based access control"},
    )

    tenant_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="NULL for system roles; tenant FK for custom roles",
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Role display name (unique per tenant, or among system roles)",
    )

    slug: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
        comment="URL-safe identifier (unique per tenant, or among system roles)",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        default=None,
        comment="Role description",
    )

    is_system: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        comment="System role (seeded, immutable). Custom tenant roles are false.",
    )

    tenant: Mapped[Optional[Tenant]] = relationship(lazy="noload")

    role_permissions: Mapped[list[RolePermission]] = relationship(
        back_populates="role",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Role(slug='{self.slug}', is_system={self.is_system})>"
