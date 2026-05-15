"""
Permission catalog table.

Source of truth for codes is `guards.permissions.Permission`. This table
exists so `role_permission` can have a real FK and the upcoming admin UI can
render the permission matrix.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from advanced_alchemy.base import UUIDv7AuditBase
from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .role_permission import RolePermission


class Permission(UUIDv7AuditBase):
    """Permission catalog entry."""

    __tablename__ = "permission"
    __table_args__ = {"comment": "Permission catalog (RBAC capability layer)"}

    code: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
        comment="Stable identifier like 'read:agents' — used as FK from role_permission",
    )

    resource_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Resource bucket (e.g. 'agents', 'collections')",
    )

    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Action verb (read, write, delete, execute, share, manage)",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )

    is_system: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="True for seeded catalog entries (cannot be deleted via UI)",
    )

    role_permissions: Mapped[list[RolePermission]] = relationship(
        back_populates="permission",
        lazy="noload",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Permission(code='{self.code}')>"
