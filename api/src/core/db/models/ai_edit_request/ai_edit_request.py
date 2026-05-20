"""One row per call to the AI entity editor.

The table records EVERY call — succeeded, schema-invalid, LLM-error —
because the dataset is useful for:

* prompt-quality eval (success rate per entity_type, common failure
  patterns),
* cost accounting (sum of ``cost_usd`` per tenant / per user),
* security review (if an AI edit produces a suspicious payload, the
  full prompt + response is preserved).

It does NOT represent the *applied* change — that's the regular audit
row, written by the existing audit listener when the user (or a future
auto-apply path) saves the new state. The bridge is the
``ai_request_id`` column on ``entity_audit_log`` (added in the same
migration).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.types import JsonB
from sqlalchemy import ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column


class AIEditRequest(UUIDv7AuditBase):
    """One row per AI-edit invocation, regardless of outcome."""

    __tablename__ = "ai_edit_request"
    __table_args__ = (
        Index(
            "ix_ai_edit_request_tenant_created",
            "tenant_id",
            "created_at",
        ),
        Index(
            "ix_ai_edit_request_tenant_actor_created",
            "tenant_id",
            "actor_id",
            "created_at",
        ),
        Index(
            "ix_ai_edit_request_tenant_entity",
            "tenant_id",
            "entity_type",
            "entity_id",
        ),
        {"comment": "Tracker for AI-assisted entity edits (Part B)"},
    )

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    actor_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("user_account.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="User who triggered the edit (NULL for system / api_key)",
    )

    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_id: Mapped[UUID] = mapped_column(nullable=False, index=True)

    instruction: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="The user-supplied natural-language instruction",
    )

    model: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Resolved model system_name (NULL = default)",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="succeeded",
        comment="'succeeded' | 'schema_invalid' | 'llm_error'",
    )

    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(12, 6), nullable=False, default=Decimal("0")
    )
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    snapshot_before: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB,
        nullable=True,
        comment="Entity state at the time the request was made",
    )
    snapshot_after: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB,
        nullable=True,
        comment="Proposed state from the LLM (NULL on failure)",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<AIEditRequest(status='{self.status}', "
            f"type='{self.entity_type}', id={self.entity_id})>"
        )
