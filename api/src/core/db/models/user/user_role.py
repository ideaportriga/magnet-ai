"""
User-Role association table definition.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.types import DateTimeUTC
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column


class UserRole(UUIDv7AuditBase):
    """Many-to-many association between User and Role."""

    __tablename__ = "user_role"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_role"),
        {"comment": "User-role assignments"},
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("user_account.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK to user_account",
    )

    role_id: Mapped[UUID] = mapped_column(
        ForeignKey("role.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK to role",
    )

    assigned_at: Mapped[datetime] = mapped_column(
        DateTimeUTC,
        nullable=False,
        default=lambda: datetime.now(UTC),
        comment="When the role was assigned",
    )

    def __repr__(self) -> str:
        return f"<UserRole(user_id='{self.user_id}', role_id='{self.role_id}')>"
