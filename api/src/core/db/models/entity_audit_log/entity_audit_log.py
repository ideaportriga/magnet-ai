"""Entity audit log — one row per CRUD mutation of an auditable business entity.

Separate from ``access_audit_log`` (which tracks access-control state changes).
This table is the source of truth for "who changed entity X, when, what, and
how to restore an earlier version".

See ``docs/AI_ENTITY_EDITING_PLAN.md`` Part A for the design.
"""

from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.types import JsonB
from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column


class EntityAuditLog(UUIDv7AuditBase):
    """One row per create/update/delete/restore of an auditable entity."""

    __tablename__ = "entity_audit_log"
    __table_args__ = (
        Index(
            "ix_entity_audit_log_tenant_entity_created",
            "tenant_id",
            "entity_type",
            "entity_id",
            "created_at",
        ),
        Index(
            "ix_entity_audit_log_tenant_created",
            "tenant_id",
            "created_at",
        ),
        Index(
            "ix_entity_audit_log_tenant_actor_created",
            "tenant_id",
            "actor_id",
            "created_at",
        ),
        {"comment": "Per-entity change history (see AI_ENTITY_EDITING_PLAN.md)"},
    )

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Tenant that owned the entity at the time of the change",
    )

    entity_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Slug of the auditable entity, e.g. 'agent', 'prompt_template'",
    )

    entity_id: Mapped[UUID] = mapped_column(
        nullable=False,
        index=True,
        comment="Primary key of the changed entity. No FK — entity may be deleted.",
    )

    action: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="'create' | 'update' | 'delete' | 'restore'",
    )

    actor_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("user_account.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="User who performed the change. NULL for system / api_key / scheduler.",
    )

    actor_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="'user' | 'api_key' | 'scheduler' | 'system' | 'background' | 'anonymous'",
    )

    actor_display: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="",
        comment="Human-readable label: email / api_client_code / 'scheduler:job_name'",
    )

    source: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="system",
        comment="'web_ui' | 'api_key' | 'scheduler' | 'system' | 'migration' | 'ai_assistant'",
    )

    request_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Correlation id (X-Request-ID) for cross-service tracing",
    )

    snapshot_before: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB,
        nullable=True,
        comment="Full entity state BEFORE the change. NULL for 'create'.",
    )

    snapshot_after: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB,
        nullable=True,
        comment="Full entity state AFTER the change. NULL for 'delete'.",
    )

    diff: Mapped[dict[str, Any]] = mapped_column(
        JsonB,
        nullable=False,
        default=dict,
        comment="Per-path diff: {'path.to.field': {'from': ..., 'to': ...}}",
    )

    ai_request_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("ai_edit_request.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment=(
            "Set when this audit row was produced by saving an AI-edit "
            "suggestion; links back to the originating ai_edit_request row. "
            "NULL for manual edits."
        ),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<EntityAuditLog(action='{self.action}', "
            f"type='{self.entity_type}', id={self.entity_id})>"
        )
