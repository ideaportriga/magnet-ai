"""
Role table definition.
"""

from __future__ import annotations

from typing import Optional

from advanced_alchemy.base import UUIDv7AuditBase
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column


class Role(UUIDv7AuditBase):
    """Role for RBAC.

    Roles are assigned to users via the UserRole association table.
    Default roles ('admin', 'user') are seeded via migration.
    """

    __tablename__ = "role"
    __table_args__ = {"comment": "Roles for role-based access control"}

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        comment="Role display name",
    )

    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
        comment="URL-safe role identifier (e.g., 'admin', 'user')",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        default=None,
        comment="Role description",
    )

    def __repr__(self) -> str:
        return f"<Role(slug='{self.slug}')>"
