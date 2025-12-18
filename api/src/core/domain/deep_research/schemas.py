"""Pydantic schemas for Deep Research Config and Run."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from core.domain.base.schemas import (
    BaseSimpleCreateSchema,
    BaseSimpleSchema,
    BaseSimpleUpdateSchema,
)


class DeepResearchConfigSchema(BaseSimpleSchema):
    """Deep Research Config schema for serialization."""

    config: Optional[dict[str, Any]] = Field(
        default=None,
        description="Deep research configuration in JSON format"
    )


class DeepResearchConfigCreateSchema(BaseSimpleCreateSchema):
    """Schema for creating a new Deep Research Config."""

    config: Optional[dict[str, Any]] = Field(
        default=None,
        description="Deep research configuration in JSON format"
    )


class DeepResearchConfigUpdateSchema(BaseSimpleUpdateSchema):
    """Schema for updating an existing Deep Research Config."""

    config: Optional[dict[str, Any]] = Field(
        default=None,
        description="Deep research configuration in JSON format"
    )


# Run schemas (extends UUIDv7AuditBase, not UUIDAuditSimpleBase)
class DeepResearchRunSchema(BaseModel):
    """Deep Research Run schema for serialization."""

    id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    client_id: Optional[str] = Field(default=None, description="Optional client-side identifier")
    status: str = Field(default="pending", description="Run status: pending, running, completed, failed")
    input: Optional[dict[str, Any]] = Field(
        default=None,
        description="Input data for the research (e.g., {'query': 'research question'})"
    )
    config: Optional[dict[str, Any]] = Field(default=None, description="Configuration snapshot used for this run")
    config_system_name: Optional[str] = Field(
        default=None,
        description="System name of the configuration used for this run",
    )
    details: Optional[dict[str, Any]] = Field(
        default=None,
        description="Run execution details (memory, iterations, result, error)"
    )


class DeepResearchRunCreateSchema(BaseModel):
    """Schema for creating a new Deep Research Run (database persistence)."""

    client_id: Optional[str] = Field(default=None, description="Optional client-side identifier")
    input: Optional[dict[str, Any]] = Field(
        default=None,
        description="Input data for the research (e.g., {'query': 'research question'})"
    )
    config: Optional[dict[str, Any]] = Field(default=None, description="Configuration snapshot used for this run")
    config_system_name: Optional[str] = Field(
        default=None,
        description="System name of the configuration used for this run",
    )


class DeepResearchRunCreateRequestSchema(BaseModel):
    """Schema for client requests to start a deep research run."""

    client_id: Optional[str] = Field(default=None, description="Optional client-side identifier")
    input: Optional[dict[str, Any]] = Field(
        default=None,
        description="Input data for the research (e.g., {'query': 'research question'})"
    )
    config: Optional[dict[str, Any]] = Field(default=None, description="Configuration override provided directly")
    config_system_name: Optional[str] = Field(
        default=None,
        description="System name of a saved configuration to use"
    )


class DeepResearchRunUpdateSchema(BaseModel):
    """Schema for updating an existing Deep Research Run."""

    status: Optional[str] = Field(default=None, description="Run status")
    details: Optional[dict[str, Any]] = Field(default=None, description="Run execution details")


class DeepResearchRunCreatedResponse(BaseModel):
    """Response returned after creating a deep research run."""

    run_id: UUID = Field(description="Identifier of the created run")
