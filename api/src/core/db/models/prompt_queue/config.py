"""Prompt Queue Config database model."""

from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from advanced_alchemy.types import JsonB
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from ..base import UUIDAuditSimpleBase


class PromptQueueConfig(UUIDAuditSimpleBase):
    """Config for a prompt queue: ordered steps, each step has multiple prompt templates."""

    __tablename__ = "prompt_queue_configs"

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Organization-tenant. Per-tenant config (Q-6).",
    )

    config: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB,
        nullable=True,
        comment="Steps with prompt_template_ids per step (JSON format)",
    )
