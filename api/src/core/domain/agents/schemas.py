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

# class WebChannel(BaseModel):
#     """Web channel schema."""
#     enabled: bool = Field(
#         default=False, description="Whether the Web channel is enabled"
#     )
#     theme: Optional[str] = Field(
#         default='siebel', description="Web Theme"
#     )
#     show_close_button: bool = Field(
#         default=True, description="Whether the Web close button is shown"
#     )
#     is_icon_hide: bool = Field(
#         default=False, description="Whether the Web icon is hidden"
#     )

# class MsTeamsChannel(BaseModel):
#     """MS Teams channel schema."""
#     enabled: bool = Field(
#         default=False, description="Whether the MS Teams channel is enabled"
#     )
#     client_id: Optional[str] = Field(
#         default=None, description="MS Teams Client ID"
#     )
#     tenant_id: Optional[str] = Field(
#         default=None, description="MS Teams Tenant ID"
#     )
#     secret_value: Optional[str] = Field(
#         default=None, description="MS Teams Secret Value"
#     )
#     secret_encrypted: Optional[str] = Field(
#         default=None, description="MS Teams Secret Encrypted"
#     )
# class SlackChannel(BaseModel):
#     """Slack channel schema."""
#     enabled: bool = Field(
#         default=False, description="Whether the Slack channel is enabled"
#     )
#     client_id: Optional[str] = Field(
#         default=None, description="Slack Client ID"
#     )
#     scopes: Optional[str] = Field(
#         default=None, description="Slack Agent Scopes"
#     )
#     token: Optional[str] = Field(
#         default=None, description="Slack Token"
#     )
#     signing_secret: Optional[str] = Field(
#         default=None, description="Slack Signing Secret"
#     )
#     client_secret: Optional[str] = Field(
#         default=None, description="Slack Client Secret"
#     )
#     state_secret: Optional[str] = Field(
#         default=None, description="Slack State Secret"
#     )
#     token_encrypted: Optional[str] = Field(
#         default=None, description="Slack Token Encrypted"
#     )
#     signing_secret_encrypted: Optional[str] = Field(
#         default=None, description="Slack Signing Secret Encrypted"
#     )
#     client_secret_encrypted: Optional[str] = Field(
#         default=None, description="Slack Client Secret Encrypted"
#     )
#     state_secret_encrypted: Optional[str] = Field(
#         default=None, description="Slack State Secret Encrypted"
#     )

# class AgentChannels(BaseModel):
#     """Agent channels schema."""
#     web: Optional[WebChannel] = Field(
#         default=None, description="Web channel"
#     )
#     ms_teams: Optional[MsTeamsChannel] = Field(
#         default=None, description="MS Teams channel"
#     )
#     slack: Optional[SlackChannel] = Field(
#         default=None, description="Slack channel"
#     )

# Pydantic schemas for serialization with variant validation
class Agent(BaseEntitySchema):
    """Agent schema for serialization."""
    # channels: Optional[AgentChannels] = Field(
    #     default=None, description="List of agent channels"
    # )
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
