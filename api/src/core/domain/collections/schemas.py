"""
Pydantic schemas for Collections validation.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from core.domain.base.schemas import (
    BaseSimpleCreateSchema,
    BaseSimpleSchema,
    BaseSimpleUpdateSchema,
)


def _coerce_json_str(v: Any) -> Any:
    """Parse a JSON string into a Python object.

    JSONB columns sometimes arrive as strings when read via SQLAlchemy
    with ``from_attributes=True`` (asyncpg codec mismatch).
    """
    if isinstance(v, str):
        try:
            return json.loads(v)
        except (json.JSONDecodeError, ValueError):
            pass
    return v


# Base mixin for common Collection fields
class CollectionFieldsMixin(BaseModel):
    """Mixin containing all common Collection fields."""

    # Collection type and model
    type: Optional[str] = Field(
        None, description="Collection type (e.g., 'documents', 'images')"
    )

    ai_model: Optional[str] = Field(
        None,
        description="Model used for processing (e.g., 'AZURE_AI_TEXT-EMBEDDING-3-SMALL')",
    )

    # Provider information
    provider_system_name: Optional[str] = Field(
        None, description="Foreign key to provider system_name"
    )

    # Configuration fields
    source: Optional[dict[str, Any]] = Field(
        None, description="Source configuration for the collection"
    )

    chunking: Optional[dict[str, Any]] = Field(
        None, description="Chunking configuration for the collection"
    )

    indexing: Optional[dict[str, Any]] = Field(
        None, description="Indexing configuration for the collection"
    )

    metadata_config: Optional[list[dict[str, Any]]] = Field(
        None, description="Metadata configuration for the collection"
    )

    # Sync timestamp
    last_synced: Optional[datetime] = Field(
        None, description="Last synced timestamp for the collection"
    )

    job_id: Optional[str] = Field(
        None, description="Job ID associated with the collection"
    )

    @field_validator("source", "chunking", "indexing", "metadata_config", mode="before")
    @classmethod
    def _parse_jsonb_strings(cls, v: Any) -> Any:
        return _coerce_json_str(v)


# Mixin for update operations with all fields optional
class CollectionUpdateFieldsMixin(BaseModel):
    """Mixin containing all Collection fields as optional for updates."""

    # Collection type and model
    type: Optional[str] = Field(
        None, description="Collection type (e.g., 'documents', 'images')"
    )

    ai_model: Optional[str] = Field(
        None,
        description="Model used for processing (e.g., 'AZURE_AI_TEXT-EMBEDDING-3-SMALL')",
    )

    # Provider information
    provider_system_name: Optional[str] = Field(
        None, description="Foreign key to provider system_name"
    )

    # Configuration fields
    source: Optional[dict[str, Any]] = Field(
        None, description="Source configuration for the collection"
    )

    chunking: Optional[dict[str, Any]] = Field(
        None, description="Chunking configuration for the collection"
    )

    indexing: Optional[dict[str, Any]] = Field(
        None, description="Indexing configuration for the collection"
    )

    metadata_config: Optional[list[dict[str, Any]]] = Field(
        None, description="Metadata configuration for the collection"
    )

    # Sync timestamp
    last_synced: Optional[datetime] = Field(
        None, description="Last synced timestamp for the collection"
    )
    job_id: Optional[str] = Field(
        None, description="Job ID associated with the collection"
    )

    @field_validator("source", "chunking", "indexing", "metadata_config", mode="before")
    @classmethod
    def _parse_jsonb_strings(cls, v: Any) -> Any:
        return _coerce_json_str(v)


# Pydantic schemas for Collections
class Collection(BaseSimpleSchema, CollectionFieldsMixin):
    """Collection schema for serialization."""


class CollectionCreate(BaseSimpleCreateSchema, CollectionFieldsMixin):
    """Schema for creating a new Collection."""


class CollectionUpdate(BaseSimpleUpdateSchema, CollectionUpdateFieldsMixin):
    """Schema for updating an existing Collection."""
