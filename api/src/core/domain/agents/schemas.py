"""
Pydantic schemas for agent validation.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from services.agents.models import AgentVariantValue
from services.entities.types import EntityVariant
from core.domain.base.schemas import (
    BaseEntityCreateSchema,
    BaseEntitySchema,
    BaseEntityUpdateSchema,
)


# class WebChannel(BaseModel):
#     """Web channel schema."""
#     enabled: bool = Field(default=False, description="Web channel enabled")
#     theme: str = Field(default="siebel", description="Web channel theme")
#     show_close_button: bool = Field(default=False, description="Web channel show close button")
#     is_icon_hide: bool = Field(default=False, description="Web channel hide icon")

# class AgentChannels(BaseModel):
#     """Agent channels schema"""
#     # temporary, for additional channels support
#     model_config = ConfigDict(extra="allow")
    
#     web: Optional[WebChannel] = Field(
#         default_factory=WebChannel, description="Web channel configuration"
#     )

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
