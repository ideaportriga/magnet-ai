"""
Pydantic schemas for AI models validation.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator

from core.domain.base.schemas import (
    BaseSimpleCreateSchema,
    BaseSimpleSchema,
    BaseSimpleUpdateSchema,
)


class RoutingConfig(BaseModel):
    """
    Routing configuration for LiteLLM integration.
    Defines rate limits, failover, caching, and load balancing settings.
    """

    # Rate limiting
    rpm: Optional[int] = Field(
        None, description="Requests per minute limit for this model"
    )
    tpm: Optional[int] = Field(
        None, description="Tokens per minute limit for this model"
    )

    # Failover configuration
    fallback_models: Optional[list[str]] = Field(
        None,
        description="List of model system_names to fallback to on failure",
    )

    # Caching
    cache_enabled: Optional[bool] = Field(
        False, description="Enable in-memory response caching"
    )
    cache_ttl: Optional[int] = Field(
        None, description="Cache TTL in seconds (default: 3600)"
    )

    # Load balancing
    priority: Optional[int] = Field(
        None, description="Priority for load balancing (lower = higher priority)"
    )
    weight: Optional[float] = Field(
        None, description="Weight for weighted load balancing (0.0-1.0)"
    )

    # Retry settings
    num_retries: Optional[int] = Field(
        None, description="Number of retries on failure (default: 3)"
    )
    retry_after: Optional[int] = Field(
        None, description="Seconds to wait before retry (default: 5)"
    )

    # Timeout
    timeout: Optional[int] = Field(
        None, description="Request timeout in seconds (default: 120)"
    )

    # Additional LiteLLM params
    litellm_params: Optional[dict[str, Any]] = Field(
        None,
        description="Additional LiteLLM parameters (api_version, custom_llm_provider, etc.)",
    )

    class Config:
        extra = "allow"


# Base mixin for common AI model fields
class AIModelFieldsMixin(BaseModel):
    """Mixin containing all common AI model fields."""

    # Provider information
    provider_name: str = Field(..., description="AI provider (e.g., azure_open_ai)")
    provider_system_name: Optional[str] = Field(
        None, description="Foreign key to provider system_name"
    )

    # Model identification
    ai_model: str = Field(..., description="Model identifier (e.g., gpt-4o)")
    display_name: str = Field(..., description="Human-readable model name")

    # Model capabilities
    json_mode: bool = Field(default=False, description="Supports JSON mode")
    json_schema: bool = Field(
        default=False, description="Supports JSON schema validation"
    )
    tool_calling: bool = Field(default=False, description="Supports tool calling")
    reasoning: bool = Field(default=False, description="Supports reasoning")

    # Type and default settings
    type: str = Field(..., description="Model type (e.g., prompts)")
    is_default: bool = Field(
        default=False, description="Is this the default model for its type"
    )
    is_active: bool = Field(
        default=True, description="Whether the model is active and available for use"
    )

    # Pricing information (stored as strings to maintain precision)
    price_input: Optional[str] = Field(None, description="Price per input unit")
    price_output: Optional[str] = Field(None, description="Price per output unit")
    price_cached: Optional[str] = Field(None, description="Price per cached input unit")
    price_reasoning: Optional[str] = Field(
        None, description="Price per reasoning output unit"
    )

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
    price_reasoning_output_unit_count: Optional[int] = Field(
        None, description="Reasoning output unit count for pricing"
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

    # Additional configurations (for embeddings vector_size, etc.)
    configs: Optional[dict] = Field(
        None,
        description="Additional model configurations (e.g., {'vector_size': 1024} for embeddings)",
    )

    # Routing and rate limiting configuration
    routing_config: Optional[RoutingConfig] = Field(
        None,
        description="Routing config: rpm, tpm, fallback_models, cache, priority, weight",
    )

    # Per-model endpoint override (virtual field — stored in routing_config.litellm_params.api_base)
    custom_endpoint: Optional[str] = Field(
        None,
        description=(
            "Custom API endpoint for this model, overriding the provider-level endpoint. "
            "Stored in routing_config.litellm_params.api_base."
        ),
    )


# Mixin for update operations with all fields optional
class AIModelUpdateFieldsMixin(BaseModel):
    """Mixin containing all AI model fields as optional for updates."""

    # Provider information
    provider_name: Optional[str] = Field(
        None, description="AI provider (e.g., azure_open_ai)"
    )
    provider_system_name: Optional[str] = Field(
        None, description="Foreign key to provider system_name"
    )

    # Model identification
    ai_model: Optional[str] = Field(None, description="Model identifier (e.g., gpt-4o)")
    display_name: Optional[str] = Field(None, description="Human-readable model name")

    # Model capabilities
    json_mode: Optional[bool] = Field(None, description="Supports JSON mode")
    json_schema: Optional[bool] = Field(
        None, description="Supports JSON schema validation"
    )
    tool_calling: Optional[bool] = Field(None, description="Supports tool calling")
    reasoning: Optional[bool] = Field(None, description="Supports reasoning")

    # Type and default settings
    type: Optional[str] = Field(None, description="Model type (e.g., prompts)")
    is_default: Optional[bool] = Field(
        None, description="Is this the default model for its type"
    )
    is_active: Optional[bool] = Field(
        None, description="Whether the model is active and available for use"
    )

    # Pricing information (stored as strings to maintain precision)
    price_input: Optional[str] = Field(None, description="Price per input unit")
    price_output: Optional[str] = Field(None, description="Price per output unit")
    price_cached: Optional[str] = Field(None, description="Price per cached input unit")
    price_reasoning: Optional[str] = Field(
        None, description="Price per reasoning output unit"
    )

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
    price_reasoning_output_unit_count: Optional[int] = Field(
        None, description="Reasoning output unit count for pricing"
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

    # Additional configurations (for embeddings vector_size, etc.)
    configs: Optional[dict] = Field(
        None,
        description="Additional model configurations (e.g., {'vector_size': 1024} for embeddings)",
    )

    # Routing and rate limiting configuration
    routing_config: Optional[RoutingConfig] = Field(
        None,
        description="Routing config: rpm, tpm, fallback_models, cache, priority, weight",
    )

    # Per-model endpoint override (virtual field — stored in routing_config.litellm_params.api_base)
    custom_endpoint: Optional[str] = Field(
        None,
        description=(
            "Custom API endpoint for this model, overriding the provider-level endpoint. "
            "Stored in routing_config.litellm_params.api_base."
        ),
    )


# Pydantic schemas for AI Models
class AIModel(BaseSimpleSchema, AIModelFieldsMixin):
    """AI Model schema for serialization."""

    @model_validator(mode="after")
    def populate_custom_endpoint_from_routing_config(self) -> "AIModel":
        """Populate custom_endpoint from routing_config.litellm_params.api_base on read."""
        if self.custom_endpoint is None and self.routing_config:
            litellm_params = self.routing_config.litellm_params or {}
            api_base = litellm_params.get("api_base") or litellm_params.get("base_url")
            if api_base:
                self.custom_endpoint = api_base
        return self


class AIModelCreate(BaseSimpleCreateSchema, AIModelFieldsMixin):
    """Schema for creating a new AI model."""

    @model_validator(mode="after")
    def inject_custom_endpoint_into_routing_config(self) -> "AIModelCreate":
        """Write custom_endpoint into routing_config.litellm_params.api_base on create."""
        if self.custom_endpoint:
            if self.routing_config is None:
                self.routing_config = RoutingConfig()
            litellm_params = dict(self.routing_config.litellm_params or {})
            litellm_params["api_base"] = self.custom_endpoint
            self.routing_config.litellm_params = litellm_params
        return self


class AIModelUpdate(BaseSimpleUpdateSchema, AIModelUpdateFieldsMixin):
    """Schema for updating an existing AI model."""

    @model_validator(mode="after")
    def inject_custom_endpoint_into_routing_config(self) -> "AIModelUpdate":
        """Write custom_endpoint into routing_config.litellm_params.api_base on update."""
        if self.custom_endpoint:
            if self.routing_config is None:
                self.routing_config = RoutingConfig()
            litellm_params = dict(self.routing_config.litellm_params or {})
            litellm_params["api_base"] = self.custom_endpoint
            self.routing_config.litellm_params = litellm_params
        return self


class AIModelSetDefaultRequest(BaseModel):
    """Schema for setting a model as default."""

    type: str = Field(..., description="Model type (e.g., prompts, embeddings)")
    system_name: str = Field(
        ..., description="System name of the model to set as default"
    )
