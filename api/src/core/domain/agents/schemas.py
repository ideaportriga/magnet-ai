"""
Pydantic schemas for agent validation.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import ConfigDict, Field, field_validator, model_serializer

from services.agents.models import AgentVariantValue
from services.entities.types import EntityVariant
from core.domain.base.schemas import (
    BaseEntityCreateSchema,
    BaseEntitySchema,
    BaseEntityUpdateSchema,
)

from core.domain.agents_channels.schemas import AgentChannels, AgentChannelsUpdate


# Pydantic schemas for serialization with variant validation
class Agent(BaseEntitySchema):
    """Agent schema for serialization."""

    # `permissions` is exposed on the wire as `_permissions` (PR 8).
    # `populate_by_name=True` lets the controller assign via the Python name.
    model_config = ConfigDict(populate_by_name=True)

    channels: Optional[AgentChannels] = Field(
        default=None, description="List of agent channels"
    )
    variants: Optional[list[EntityVariant[AgentVariantValue]]] = Field(
        default=None, description="List of agent variants"
    )
    # Record-level fields (PR 8). `_permissions` is attached by the
    # controller serializer because computing it needs the request user.
    # UUIDs are stringified for wire format.
    owner_id: Optional[str] = Field(default=None, description="Owner user id")
    department_id: Optional[str] = Field(
        default=None, description="Owning department id"
    )
    visibility: Optional[str] = Field(
        default="tenant",
        description="'private' | 'department' | 'tenant'",
    )
    tenant_id: Optional[str] = Field(default=None, description="Owning tenant id")
    permissions: Optional[dict[str, bool]] = Field(
        default=None,
        alias="_permissions",
        serialization_alias="_permissions",
        description="Per-record action flags (view/edit/delete/share)",
    )

    @field_validator("owner_id", "department_id", "tenant_id", mode="before")
    @classmethod
    def _stringify_uuid(cls, value):
        """Accept UUID from SQLAlchemy and serialize as str."""
        if isinstance(value, UUID):
            return str(value)
        return value

    @model_serializer(mode="wrap")
    def _rename_permissions(self, handler):
        """Emit the `permissions` field on the wire as `_permissions` (PR 8).

        Pydantic's `serialization_alias` only fires when `by_alias=True` is
        passed to model_dump — Litestar's default serializer doesn't. This
        wrap-serializer renames the key after the default dump runs.
        """
        result = handler(self)
        if isinstance(result, dict) and "permissions" in result:
            result["_permissions"] = result.pop("permissions")
        return result


class AgentCreate(BaseEntityCreateSchema):
    """Schema for creating a new agent."""

    # chanels are not included in create schema to avoid copying chanels
    # when cloning new agent from existing agent
    variants: Optional[list[EntityVariant[AgentVariantValue]]] = Field(
        default=None, description="List of agent variants"
    )


class AgentUpdate(BaseEntityUpdateSchema):
    """Schema for updating an existing agent."""

    channels: Optional[AgentChannelsUpdate] = Field(
        default=None, description="List of agent channels"
    )
    variants: Optional[list[EntityVariant[AgentVariantValue]]] = Field(
        default=None, description="List of agent variants"
    )
