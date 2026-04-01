"""
User-Group association table definition.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.types import DateTimeUTC
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column


class UserGroup(UUIDv7AuditBase):
    """Many-to-many association between User and Group with a role within the group."""

    __tablename__ = "user_group_member"
    __table_args__ = (
        UniqueConstraint("user_id", "group_id", name="uq_user_group_member"),
        {"comment": "User-group membership with role"},
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("user_account.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK to user_account",
    )

    group_id: Mapped[UUID] = mapped_column(
        ForeignKey("user_group.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK to user_group",
    )

    role_in_group: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="member",
        comment="Role within the group: 'member' or 'owner'",
    )

    assigned_at: Mapped[datetime] = mapped_column(
        DateTimeUTC,
        nullable=False,
        default=lambda: datetime.now(UTC),
        comment="When the user was added to the group",
    )

    def __repr__(self) -> str:
        return f"<UserGroup(user_id='{self.user_id}', group_id='{self.group_id}', role='{self.role_in_group}')>"
