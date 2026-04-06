"""
Base Pydantic schemas for entities that inherit from UUIDAuditEntityBase.

These schemas provide a consistent structure for all entities and eliminate code duplication.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, field_serializer, model_validator

logger = logging.getLogger(__name__)


class SecretsEncryptedMixin(BaseModel):
    """
    Mixin for masking encrypted secrets in API responses.

    This mixin provides a field serializer that masks the values of encrypted secrets
    while preserving the keys. Used in Response schemas to prevent exposing sensitive data.
    """

    @field_serializer("secrets_encrypted", when_used="always", check_fields=False)
    def serialize_secrets_encrypted(
        self, value: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, str]]:
        """Serialize secrets to show keys with masked values."""
        if value is None:
            return None
        if isinstance(value, dict):
            return {key: "" for key in value.keys()}
        return None


class BaseSchema(BaseModel):
    """
    Base schema for all entities.
    """

    id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def _decode_jsonb_strings(cls, data: Any) -> Any:
        """Auto-parse JSONB fields stored as double-encoded strings in legacy data.

        Some historical records have JSONB columns saved as JSON string literals
        (e.g. '"[{...}]"' instead of '[{...}]'). This validator transparently
        fixes them at read time so that to_schema() never crashes on legacy data.

        Also handles the ``from_attributes=True`` path where *data* is a
        SQLAlchemy model instance rather than a dict.
        """
        if isinstance(data, dict):
            items = data
        elif hasattr(data, "__dict__") and not isinstance(data, BaseModel):
            # from_attributes=True (e.g. SQLAlchemy model) — extract only
            # the fields declared on this Pydantic schema to avoid triggering
            # lazy-loaded relationships.
            items = {}
            for key in cls.model_fields:
                value = getattr(data, key, None)
                items[key] = value
        else:
            return data

        for key, value in items.items():
            if isinstance(value, str) and value and value[0] in ("{", "["):
                try:
                    items[key] = json.loads(value)
                except (json.JSONDecodeError, ValueError):
                    pass
        return items


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
    created_by and updated_by are set by the controller from audit_username.
    """

    # Fields for creation
    name: str
    description: Optional[str] = None
    system_name: str
    category: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None


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
    updated_by: Optional[str] = None


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
