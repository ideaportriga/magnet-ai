"""
Role-Permission association table.

Many-to-many between role and permission. FK on `permission_code` references
the natural key of `permission.code`. ON DELETE CASCADE: removing a role
clears its permission grants; removing a permission code from the catalog
(rare, requires migration) drops the same code from every role.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .permission import Permission
    from .role import Role


class RolePermission(UUIDv7AuditBase):
    """Grants a `permission` to a `role`."""

    __tablename__ = "role_permission"
    __table_args__ = (
        UniqueConstraint("role_id", "permission_code", name="uq_role_permission"),
        {"comment": "Role-permission grants"},
    )

    role_id: Mapped[UUID] = mapped_column(
        ForeignKey("role.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    permission_code: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("permission.code", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role: Mapped[Role] = relationship(back_populates="role_permissions", lazy="noload")
    permission: Mapped[Permission] = relationship(
        back_populates="role_permissions", lazy="noload"
    )

    def __repr__(self) -> str:
        return (
            f"<RolePermission(role_id={self.role_id}, code='{self.permission_code}')>"
        )
