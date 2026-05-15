"""User ↔ Department membership."""

from __future__ import annotations

from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column


class UserDepartment(UUIDv7AuditBase):
    """Many-to-many with `is_lead` flag.

    Leads get elevated permissions on department-visible records (per PR 8
    step 9 of the algorithm). The redundant `tenant_id` mirrors the user's
    and department's tenant for fast tenant-scoped queries / RLS.
    """

    __tablename__ = "user_department"
    __table_args__ = (
        UniqueConstraint("user_id", "department_id", name="uq_user_department"),
        {"comment": "Membership of users in departments"},
    )

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("user_account.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    department_id: Mapped[UUID] = mapped_column(
        ForeignKey("department.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    is_lead: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        comment="Department lead — gets edit/delete/share on dept records",
    )

    def __repr__(self) -> str:
        return f"<UserDepartment(user={self.user_id}, dept={self.department_id})>"
