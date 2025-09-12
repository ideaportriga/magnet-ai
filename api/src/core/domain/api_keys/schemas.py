"""
Pydantic schemas for API Keys validation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Base schemas without inheritance from core base schemas
class APIKeyBaseSchema(BaseModel):
    """Base schema for API Key with common fields."""

    id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None


class APIKeyFieldsMixin(BaseModel):
    """Mixin containing all common API Key fields."""

    name: str = Field(..., description="API key name", max_length=255)

    # Key identification and security
    hash: str = Field(
        ...,
        description="SHA-256 hash of the API key",
        max_length=64,
    )

    value_masked: str = Field(
        ...,
        description="Masked version of the API key (e.g., '...Gpys')",
        max_length=20,
    )

    expires_at: Optional[datetime] = Field(None, description="Expiration date/time")

    is_active: bool = Field(True, description="Whether the API key is active")

    notes: Optional[str] = Field(None, description="Additional notes about the API key")


# Mixin for update operations with all fields optional
class APIKeyUpdateFieldsMixin(BaseModel):
    """Mixin containing all API Key fields as optional for updates."""

    name: Optional[str] = Field(None, description="API key name", max_length=255)

    # Key identification and security
    hash: Optional[str] = Field(
        None,
        description="SHA-256 hash of the API key",
        max_length=64,
    )

    value_masked: Optional[str] = Field(
        None,
        description="Masked version of the API key (e.g., '...Gpys')",
        max_length=20,
    )

    expires_at: Optional[datetime] = Field(None, description="Expiration date/time")

    is_active: Optional[bool] = Field(None, description="Whether the API key is active")

    notes: Optional[str] = Field(None, description="Additional notes about the API key")


# Pydantic schemas for API Keys
class APIKey(APIKeyBaseSchema, APIKeyFieldsMixin):
    """API Key schema for serialization."""


class APIKeyCreate(APIKeyFieldsMixin):
    """Schema for creating a new API Key."""


class APIKeyUpdate(APIKeyUpdateFieldsMixin):
    """Schema for updating an existing API Key."""
