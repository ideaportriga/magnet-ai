"""
Pydantic schemas for Collections validation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from core.domain.base.schemas import (
    BaseSimpleCreateSchema,
    BaseSimpleSchema,
    BaseSimpleUpdateSchema,
)


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

    # Sync timestamp
    last_synced: Optional[datetime] = Field(
        None, description="Last synced timestamp for the collection"
    )

    job_id: Optional[str] = Field(
        None, description="Job ID associated with the collection"
    )


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

    # Sync timestamp
    last_synced: Optional[datetime] = Field(
        None, description="Last synced timestamp for the collection"
    )
    job_id: Optional[str] = Field(
        None, description="Job ID associated with the collection"
    )


# Pydantic schemas for Collections
class Collection(BaseSimpleSchema, CollectionFieldsMixin):
    """Collection schema for serialization."""


class CollectionCreate(BaseSimpleCreateSchema, CollectionFieldsMixin):
    """Schema for creating a new Collection."""


class CollectionUpdate(BaseSimpleUpdateSchema, CollectionUpdateFieldsMixin):
    """Schema for updating an existing Collection."""
