"""
Base domain module.

Provides base Pydantic schemas for entities that inherit from UUIDAuditEntityBase.
"""

from .schemas import (
    BaseEntityCreateSchema,
    BaseEntitySchema,
    BaseEntityUpdateSchema,
)

__all__ = [
    "BaseEntitySchema",
    "BaseEntityCreateSchema",
    "BaseEntityUpdateSchema",
]
