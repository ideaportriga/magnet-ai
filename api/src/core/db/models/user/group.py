"""
Group table definition.
"""

from __future__ import annotations

from typing import Optional

from advanced_alchemy.base import UUIDv7AuditBase
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column


class Group(UUIDv7AuditBase):
    """Group for organizing users.

    Groups allow logical grouping of users for access control
    and organizational purposes.
    """

    __tablename__ = "user_group"
    __table_args__ = {"comment": "User groups for organizational access control"}

    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        comment="Group name",
    )

    slug: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        comment="URL-safe group identifier",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        default=None,
        comment="Group description",
    )

    def __repr__(self) -> str:
        return f"<Group(slug='{self.slug}')>"
