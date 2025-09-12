"""
Base Pydantic schemas for entities that inherit from UUIDAuditEntityBase.

These schemas provide a consistent structure for all entities and eliminate code duplication.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel


class BaseSchema(BaseModel):
    """
    Base schema for all entities.
    """

    id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None


# Simple schemas
class BaseSimpleSchema(BaseSchema):
    """
    Base schema for simple entities that inherit from UUIDAuditSimpleBase.

    Includes fields for id, created_at, updated_at, created_by, and updated_by.
    """

    name: str
    description: Optional[str] = None
    system_name: str
    category: Optional[str] = None


class BaseSimpleCreateSchema(BaseModel):
    """
    Base schema for creating simple entities that inherit from UUIDAuditSimpleBase.

    Excludes auto-generated fields (id, created_at, updated_at).
    """

    # Fields for creation
    name: str
    description: Optional[str] = None
    system_name: str
    category: Optional[str] = None


class BaseSimpleUpdateSchema(BaseModel):
    """
    Base schema for updating simple entities that inherit from UUIDAuditSimpleBase.

    All fields are optional for partial updates.
    """

    # All fields are optional for updates
    name: Optional[str] = None
    description: Optional[str] = None
    system_name: Optional[str] = None
    category: Optional[str] = None


# Base schemas with variants


class BaseEntitySchema(BaseSimpleSchema):
    """
    Base schema for entities that inherit from UUIDAuditEntityBase.

    Includes all fields from UUIDAuditBase (id, created_at, updated_at)
    and UUIDAuditEntityBase (name, description, system_name, active_variant, category, variants).
    """

    active_variant: Optional[str] = None
    variants: Optional[List[dict[str, Any]]] = None


class BaseEntityCreateSchema(BaseSimpleCreateSchema):
    """
    Base schema for creating entities that inherit from UUIDAuditEntityBase.

    Excludes auto-generated fields (id, created_at, updated_at).
    """

    active_variant: Optional[str] = None
    variants: Optional[List[dict[str, Any]]] = None


class BaseEntityUpdateSchema(BaseSimpleUpdateSchema):
    """
    Base schema for updating entities that inherit from UUIDAuditEntityBase.

    All fields are optional for partial updates.
    """

    active_variant: Optional[str] = None
    variants: Optional[List[dict[str, Any]]] = None
