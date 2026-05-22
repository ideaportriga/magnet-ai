"""
AI Models table definition.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from uuid import UUID

from advanced_alchemy.types import JsonB
from sqlalchemy import (
    Boolean,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.audit.mixin import Auditable

from ..base import UUIDAuditSimpleBase

if TYPE_CHECKING:
    from ..provider import Provider


class AIModel(UUIDAuditSimpleBase, Auditable):
    __audit_entity_type__ = "ai_model"
    """
    AI Model entity for storing AI model configurations and pricing information.

    Based on the AI model JSON structure with provider, pricing, and capabilities info.
    """

    __tablename__ = "ai_models"
    __table_args__ = (
        # Composite FK to providers (tenant_id, system_name). Replaces the
        # legacy single-column FK that targeted the now-removed global
        # UNIQUE on providers.system_name.
        ForeignKeyConstraint(
            ["tenant_id", "provider_system_name"],
            ["providers.tenant_id", "providers.system_name"],
            name="fk_ai_models_provider_tenant_system_name",
            ondelete="CASCADE",
        ),
        Index("ix_ai_models_tenant_id", "tenant_id"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"),
        nullable=False,
        comment="Organization-tenant. Inherited from parent provider row.",
    )

    # Foreign key to Provider by (tenant_id, system_name) — see __table_args__.
    provider_system_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Provider system_name (composite FK with tenant_id)",
        index=True,
    )

    # Relationship to Provider (named provider_rel to avoid conflict with provider_name field in schemas)
    provider_rel: Mapped[Optional["Provider"]] = relationship(
        "Provider",
        back_populates="ai_models",
        foreign_keys=[provider_system_name],
        primaryjoin=(
            "and_(AIModel.tenant_id == Provider.tenant_id, "
            "AIModel.provider_system_name == Provider.system_name)"
        ),
    )

    # Provider information (legacy field - consider migrating to use provider relationship)
    provider_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="AI provider (e.g., azure_open_ai)",
        index=True,
    )

    # Model identification
    ai_model: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Model identifier (e.g., gpt-4o)",
        index=True,
    )
    display_name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Human-readable model name", index=True
    )

    # Model capabilities
    json_mode: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="Supports JSON mode"
    )
    json_schema: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Supports JSON schema validation",
    )
    tool_calling: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="Supports tool calling"
    )

    reasoning: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="Supports reasoning"
    )

    diarization: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="Supports speaker diarization"
    )

    # Type and default settings
    type: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Model type (e.g., prompts)", index=True
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Is this the default model for its type",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        comment="Whether the model is active and available for use",
    )

    # Pricing information (stored as strings to maintain precision)
    price_input: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="Price per input unit"
    )
    price_output: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="Price per output unit"
    )
    price_cached: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="Price per cached input unit"
    )
    price_reasoning: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="Price per reasoning output unit"
    )

    # Unit counts for pricing
    price_standard_input_unit_count: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Standard input unit count for pricing"
    )
    price_cached_input_unit_count: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Cached input unit count for pricing"
    )
    price_standard_output_unit_count: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Standard output unit count for pricing"
    )
    price_reasoning_output_unit_count: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Reasoning output unit count for pricing"
    )

    # Unit names
    price_input_unit_name: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Input price unit name (e.g., tokens)"
    )
    price_output_unit_name: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Output price unit name (e.g., tokens)"
    )

    # Resources and documentation
    resources: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="URL to pricing/documentation resources"
    )

    # Additional configurations (for embeddings vector_size, etc.)
    configs: Mapped[Optional[dict]] = mapped_column(
        JsonB,
        nullable=True,
        comment="Additional model configurations (e.g., vector_size for embeddings)",
    )

    # Routing and rate limiting configuration for LiteLLM integration
    routing_config: Mapped[Optional[dict]] = mapped_column(
        JsonB,
        nullable=True,
        comment="Routing config: rpm, tpm, fallback_models, cache, priority, weight",
    )

    def __repr__(self) -> str:
        return f"<AIModel(system_name='{self.system_name}', provider='{self.provider_name}', ai_model='{self.ai_model}')>"
