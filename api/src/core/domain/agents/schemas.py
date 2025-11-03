"""
Pydantic schemas for agent validation.
"""

from __future__ import annotations

from typing import Optional

from pydantic import Field

from services.agents.models import AgentVariantValue
from services.entities.types import EntityVariant
from core.domain.base.schemas import (
    BaseEntityCreateSchema,
    BaseEntitySchema,
    BaseEntityUpdateSchema,
)


# Pydantic schemas for serialization with variant validation
class Agent(BaseEntitySchema):
    """Agent schema for serialization."""
    channels: Optional[dict] = Field(
        default=None, description="List of agent channels"
    )
    variants: Optional[list[EntityVariant[AgentVariantValue]]] = Field(
        default=None, description="List of agent variants"
    )


class AgentCreate(BaseEntityCreateSchema):
    """Schema for creating a new agent."""
    channels: Optional[dict] = Field(
        default=None, description="List of agent channels"
    )
    variants: Optional[list[EntityVariant[AgentVariantValue]]] = Field(
        default=None, description="List of agent variants"
    )


class AgentUpdate(BaseEntityUpdateSchema):
    """Schema for updating an existing agent."""
    channels: Optional[dict] = Field(
        default=None, description="List of agent channels"
    )
    variants: Optional[list[EntityVariant[AgentVariantValue]]] = Field(
        default=None, description="List of agent variants"
    )
