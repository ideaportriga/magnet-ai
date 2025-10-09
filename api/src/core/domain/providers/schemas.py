"""
Pydantic schemas for Providers validation.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from core.domain.base.schemas import (
    BaseSimpleCreateSchema,
    BaseSimpleSchema,
    BaseSimpleUpdateSchema,
    SecretsEncryptedMixin,
)


# Base mixin for common Provider fields
class ProviderFieldsMixin(BaseModel):
    """Mixin containing all common Provider fields."""

    # Provider type
    type: Optional[str] = Field(
        None, description="Provider type (e.g., 'openai', 'azure', 'anthropic')"
    )

    # Connection configuration (non-sensitive)
    connection_config: Optional[dict[str, Any]] = Field(
        None, description="Provider configuration (non-sensitive settings)"
    )

    # Encrypted credentials and sensitive data
    secrets_encrypted: Optional[dict[str, Any]] = Field(
        None, description="Encrypted credentials and sensitive connection data"
    )

    # Additional metadata
    metadata_info: Optional[dict[str, Any]] = Field(
        None, description="Additional metadata about the provider"
    )


# Mixin for update operations with all fields optional
class ProviderUpdateFieldsMixin(BaseModel):
    """Mixin containing all Provider fields as optional for updates."""

    # Provider type
    type: Optional[str] = Field(
        None, description="Provider type (e.g., 'openai', 'azure', 'anthropic')"
    )

    # Connection configuration (non-sensitive)
    connection_config: Optional[dict[str, Any]] = Field(
        None, description="Provider configuration (non-sensitive settings)"
    )

    # Encrypted credentials and sensitive data
    secrets_encrypted: Optional[dict[str, Any]] = Field(
        None, description="Encrypted credentials and sensitive connection data"
    )

    # Additional metadata
    metadata_info: Optional[dict[str, Any]] = Field(
        None, description="Additional metadata about the provider"
    )


# Pydantic schemas for Providers
class Provider(BaseSimpleSchema, ProviderFieldsMixin):
    """Provider schema for serialization."""


class ProviderResponse(BaseSimpleSchema, SecretsEncryptedMixin):
    """Provider schema for API responses with masked secrets."""

    # Provider type
    type: Optional[str] = Field(
        None, description="Provider type (e.g., 'openai', 'azure', 'anthropic')"
    )

    # Connection configuration (non-sensitive)
    connection_config: Optional[dict[str, Any]] = Field(
        None, description="Provider configuration (non-sensitive settings)"
    )

    # Encrypted credentials and sensitive data
    secrets_encrypted: Optional[Dict[str, str]] = Field(
        None, description="Encrypted credentials with masked values"
    )

    # Additional metadata
    metadata_info: Optional[dict[str, Any]] = Field(
        None, description="Additional metadata about the provider"
    )


class ProviderCreate(BaseSimpleCreateSchema, ProviderFieldsMixin):
    """Schema for creating a new Provider."""


class ProviderUpdate(BaseSimpleUpdateSchema, ProviderUpdateFieldsMixin):
    """Schema for updating an existing Provider."""
