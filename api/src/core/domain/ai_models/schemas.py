"""
Pydantic schemas for AI models validation.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from core.domain.base.schemas import (
    BaseSimpleCreateSchema,
    BaseSimpleSchema,
    BaseSimpleUpdateSchema,
)


# Base mixin for common AI model fields
class AIModelFieldsMixin(BaseModel):
    """Mixin containing all common AI model fields."""

    # Provider information
    provider_name: str = Field(..., description="AI provider (e.g., azure_open_ai)")
    provider_system_name: Optional[str] = Field(None, description="Foreign key to provider system_name")

    # Model identification
    ai_model: str = Field(..., description="Model identifier (e.g., gpt-4o)")
    display_name: str = Field(..., description="Human-readable model name")

    # Model capabilities
    json_mode: bool = Field(default=False, description="Supports JSON mode")
    json_schema: bool = Field(
        default=False, description="Supports JSON schema validation"
    )

    # Type and default settings
    type: str = Field(..., description="Model type (e.g., prompts)")
    is_default: bool = Field(
        default=False, description="Is this the default model for its type"
    )

    # Pricing information (stored as strings to maintain precision)
    price_input: Optional[str] = Field(None, description="Price per input unit")
    price_output: Optional[str] = Field(None, description="Price per output unit")
    price_cached: Optional[str] = Field(None, description="Price per cached input unit")

    # Unit counts for pricing
    price_standard_input_unit_count: Optional[int] = Field(
        None, description="Standard input unit count for pricing"
    )
    price_cached_input_unit_count: Optional[int] = Field(
        None, description="Cached input unit count for pricing"
    )
    price_standard_output_unit_count: Optional[int] = Field(
        None, description="Standard output unit count for pricing"
    )

    # Unit names
    price_input_unit_name: Optional[str] = Field(
        None, description="Input price unit name (e.g., tokens)"
    )
    price_output_unit_name: Optional[str] = Field(
        None, description="Output price unit name (e.g., tokens)"
    )

    # Resources and documentation
    resources: Optional[str] = Field(
        None, description="URL to pricing/documentation resources"
    )


# Mixin for update operations with all fields optional
class AIModelUpdateFieldsMixin(BaseModel):
    """Mixin containing all AI model fields as optional for updates."""

    # Provider information
    provider_name: Optional[str] = Field(
        None, description="AI provider (e.g., azure_open_ai)"
    )
    provider_system_name: Optional[str] = Field(None, description="Foreign key to provider system_name")

    # Model identification
    ai_model: Optional[str] = Field(None, description="Model identifier (e.g., gpt-4o)")
    display_name: Optional[str] = Field(None, description="Human-readable model name")

    # Model capabilities
    json_mode: Optional[bool] = Field(None, description="Supports JSON mode")
    json_schema: Optional[bool] = Field(
        None, description="Supports JSON schema validation"
    )

    # Type and default settings
    type: Optional[str] = Field(None, description="Model type (e.g., prompts)")
    is_default: Optional[bool] = Field(
        None, description="Is this the default model for its type"
    )

    # Pricing information (stored as strings to maintain precision)
    price_input: Optional[str] = Field(None, description="Price per input unit")
    price_output: Optional[str] = Field(None, description="Price per output unit")
    price_cached: Optional[str] = Field(None, description="Price per cached input unit")

    # Unit counts for pricing
    price_standard_input_unit_count: Optional[int] = Field(
        None, description="Standard input unit count for pricing"
    )
    price_cached_input_unit_count: Optional[int] = Field(
        None, description="Cached input unit count for pricing"
    )
    price_standard_output_unit_count: Optional[int] = Field(
        None, description="Standard output unit count for pricing"
    )

    # Unit names
    price_input_unit_name: Optional[str] = Field(
        None, description="Input price unit name (e.g., tokens)"
    )
    price_output_unit_name: Optional[str] = Field(
        None, description="Output price unit name (e.g., tokens)"
    )

    # Resources and documentation
    resources: Optional[str] = Field(
        None, description="URL to pricing/documentation resources"
    )


# Pydantic schemas for AI Models
class AIModel(BaseSimpleSchema, AIModelFieldsMixin):
    """AI Model schema for serialization."""


class AIModelCreate(BaseSimpleCreateSchema, AIModelFieldsMixin):
    """Schema for creating a new AI model."""


class AIModelUpdate(BaseSimpleUpdateSchema, AIModelUpdateFieldsMixin):
    """Schema for updating an existing AI model."""
