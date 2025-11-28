"""
Pydantic schemas for Traces validation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# Base schema for Trace entity matching the SQLAlchemy model
class TraceBaseSchema(BaseModel):
    """
    Base schema for Trace entity matching the database model structure.
    Includes audit fields from AuditColumns mixin.
    """

    id: Optional[str] = Field(None, description="Unique identifier for the trace")
    created_at: Optional[datetime] = Field(
        None, description="Record creation timestamp"
    )
    updated_at: Optional[datetime] = Field(
        None, description="Record last update timestamp"
    )


# Base mixin for common Trace fields
class TraceFieldsMixin(BaseModel):
    """Mixin containing all common Trace fields."""

    # Core trace information
    name: Optional[str] = Field(
        None, description="Trace name (e.g., 'NPS Feedback Summary')"
    )
    type: Optional[str] = Field(
        None, description="Trace type (e.g., 'prompt-template', 'chat', 'span')"
    )
    status: Optional[str] = Field(
        None, description="Trace execution status (e.g., 'success', 'error', 'running')"
    )

    # Source and channel information
    channel: Optional[str] = Field(
        None, description="Execution channel (e.g., 'production', 'development')"
    )
    source: Optional[str] = Field(
        None, description="Trace source (e.g., 'Runtime API', 'Web UI')"
    )

    # User information
    user_id: Optional[str] = Field(None, description="User or API key identifier")

    # Timing information
    start_time: Optional[datetime] = Field(
        None, description="Trace execution start time"
    )
    end_time: Optional[datetime] = Field(None, description="Trace execution end time")
    latency: Optional[float] = Field(
        None, description="Execution latency in milliseconds"
    )

    # Cost tracking
    cost_details: Optional[dict] = Field(
        None,
        description="Cost breakdown including chat, embed, rerank, and total costs",
    )

    # Additional data
    extra_data: Optional[dict] = Field(
        None, description="Additional trace metadata and custom fields"
    )

    # Spans data - nested trace information
    spans: Optional[list[dict]] = Field(
        None, description="List of trace spans with detailed execution information"
    )


# Mixin for create operations with required core fields
class TraceCreateFieldsMixin(BaseModel):
    """Mixin containing Trace fields for creation with required core fields."""

    # Core trace information - required for creation
    name: str = Field(..., description="Trace name (e.g., 'NPS Feedback Summary')")
    type: str = Field(
        ..., description="Trace type (e.g., 'prompt-template', 'chat', 'span')"
    )
    status: str = Field(
        ..., description="Trace execution status (e.g., 'success', 'error', 'running')"
    )

    # Source and channel information
    channel: Optional[str] = Field(
        None, description="Execution channel (e.g., 'production', 'development')"
    )
    source: Optional[str] = Field(
        None, description="Trace source (e.g., 'Runtime API', 'Web UI')"
    )

    # User information
    user_id: Optional[str] = Field(None, description="User or API key identifier")

    # Timing information
    start_time: Optional[datetime] = Field(
        None, description="Trace execution start time"
    )
    end_time: Optional[datetime] = Field(None, description="Trace execution end time")
    latency: Optional[float] = Field(
        None, description="Execution latency in milliseconds"
    )

    # Cost tracking
    cost_details: Optional[dict] = Field(
        None,
        description="Cost breakdown including chat, embed, rerank, and total costs",
    )

    # Additional data
    extra_data: Optional[dict] = Field(
        None, description="Additional trace metadata and custom fields"
    )

    # Spans data - nested trace information
    spans: Optional[list[dict]] = Field(
        None, description="List of trace spans with detailed execution information"
    )


# Mixin for update operations with all fields optional
class TraceUpdateFieldsMixin(BaseModel):
    """Mixin containing all Trace fields as optional for updates."""

    # Core trace information
    name: Optional[str] = Field(
        None, description="Trace name (e.g., 'NPS Feedback Summary')"
    )
    type: Optional[str] = Field(
        None, description="Trace type (e.g., 'prompt-template', 'chat', 'span')"
    )
    status: Optional[str] = Field(
        None, description="Trace execution status (e.g., 'success', 'error', 'running')"
    )

    # Source and channel information
    channel: Optional[str] = Field(
        None, description="Execution channel (e.g., 'production', 'development')"
    )
    source: Optional[str] = Field(
        None, description="Trace source (e.g., 'Runtime API', 'Web UI')"
    )

    # User information
    user_id: Optional[str] = Field(None, description="User or API key identifier")

    # Timing information
    start_time: Optional[datetime] = Field(
        None, description="Trace execution start time"
    )
    end_time: Optional[datetime] = Field(None, description="Trace execution end time")
    latency: Optional[float] = Field(
        None, description="Execution latency in milliseconds"
    )

    # Cost tracking
    cost_details: Optional[dict] = Field(
        None,
        description="Cost breakdown including chat, embed, rerank, and total costs",
    )

    # Additional data
    extra_data: Optional[dict] = Field(
        None, description="Additional trace metadata and custom fields"
    )

    # Spans data - nested trace information
    spans: Optional[list[dict]] = Field(
        None, description="List of trace spans with detailed execution information"
    )


# Pydantic schemas for Traces
class Trace(TraceBaseSchema, TraceFieldsMixin):
    """Trace schema for serialization."""


class TraceCreate(TraceCreateFieldsMixin):
    """Schema for creating a new trace."""


class TraceUpdate(TraceUpdateFieldsMixin):
    """Schema for updating an existing trace."""
