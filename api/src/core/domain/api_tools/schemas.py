"""
Pydantic schemas for API tools validation.
"""

from __future__ import annotations

from http import HTTPMethod
from typing import Any, List, Optional

from pydantic import BaseModel, Field

from core.domain.base.schemas import (
    BaseEntityCreateSchema,
    BaseEntitySchema,
    BaseEntityUpdateSchema,
)
from services.api_tools.types import ApiTool as ApiToolType


# Pydantic schemas for serialization with variant validation
class ApiTool(BaseEntitySchema, ApiToolType):
    """API tool schema for serialization."""



class ApiToolCreate(BaseEntityCreateSchema, ApiToolType):
    """Schema for creating a new API tool."""



class ApiToolUpdate(BaseEntityUpdateSchema, ApiToolType):
    """Schema for updating an existing API tool."""
