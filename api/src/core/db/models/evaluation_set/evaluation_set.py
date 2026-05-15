from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from advanced_alchemy.types import JsonB
from sqlalchemy import CheckConstraint, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import UUIDAuditSimpleBase

if TYPE_CHECKING:
    from ..department.department import Department
    from ..tenant.tenant import Tenant
    from ..user.user import User


class EvaluationSet(UUIDAuditSimpleBase):
    """Tenant + record-level scoped evaluation set (PR 10 rollout)."""

    __tablename__ = "evaluation_sets"
    __table_args__ = (
        Index(
            "uq_evaluation_sets_system_name_per_tenant",
            "tenant_id",
            "system_name",
            unique=True,
        ),
        Index("ix_evaluation_sets_tenant_id", "tenant_id"),
        Index("ix_evaluation_sets_owner_id", "owner_id"),
        Index("ix_evaluation_sets_department_id", "department_id"),
        CheckConstraint(
            "visibility IN ('private', 'department', 'tenant')",
            name="ck_evaluation_sets_visibility",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="RESTRICT"),
        nullable=False,
    )
    system_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="System name (unique within tenant)",
    )
    owner_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("user_account.id", ondelete="SET NULL"),
        nullable=True,
    )
    department_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("department.id", ondelete="SET NULL"),
        nullable=True,
    )
    visibility: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="tenant",
        server_default="tenant",
    )

    tenant: Mapped["Tenant"] = relationship(lazy="noload")
    owner: Mapped[Optional["User"]] = relationship(lazy="noload")
    department: Mapped[Optional["Department"]] = relationship(lazy="noload")

    type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Type of evaluation set (e.g., 'test', 'validation')",
    )
    items: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(
        JsonB, nullable=True, comment="List of items in the evaluation set"
    )
