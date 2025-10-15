"""
Base classes for SQLAlchemy models.
"""

from __future__ import annotations

from collections.abc import Hashable
from typing import Any, Optional

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.mixins import UniqueMixin
from advanced_alchemy.types import JsonB
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.elements import ColumnElement


class UUIDAuditSimpleBase(UUIDv7AuditBase, UniqueMixin):
    """
    Base class for simple entities with common fields.

    Inherits from UUIDAuditBase (id, created_at, updated_at) and UniqueMixin for unique system_name handling.
    Adds:
    - name: entity name
    - description: entity description
    - system_name: system name of the entity (unique)
    - category: entity category
    """

    __abstract__ = True

    # Main fields
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Entity name", index=True
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Entity description", index=True
    )
    system_name: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, comment="System name of the entity"
    )
    category: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Entity category"
    )
    created_by: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True, comment="ID of the user who created the entity"
    )
    updated_by: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True, comment="ID of the user who last updated the entity"
    )

    @classmethod
    def unique_hash(cls, system_name: str, **kwargs: Any) -> Hashable:
        """Generate a unique hash for deduplication based on system_name."""
        return system_name.lower().strip()

    @classmethod
    def unique_filter(
        cls,
        system_name: str,
        **kwargs: Any,
    ) -> ColumnElement[bool]:
        """SQL filter for finding existing records by system_name."""
        return cls.system_name == system_name


class UUIDAuditEntityBase(UUIDAuditSimpleBase):
    """
    Base class for entities with common fields.

    Inherits from UUIDAuditSimpleBase (which includes id, created_at, updated_at, name, description, system_name, etc.).
    Adds:
    - active_variant: name of the active variant
    - variants: JSON field for storing list of variants with Pydantic validation
    """

    __abstract__ = True

    # Additional fields specific to entities with variants
    active_variant: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Active variant name"
    )
    # Field for storing variants in JSONB format
    variants: Mapped[Optional[list[Any]]] = mapped_column(
        JsonB, nullable=True, comment="List of variants in JSON format"
    )
