"""
Pydantic schemas for Metrics validation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from core.domain.base.schemas import BaseSchema


# Base mixin for common Metric fields
class MetricFieldsMixin(BaseModel):
    """Mixin containing all common Metric fields."""

    # Feature information
    feature_type: str = Field(
        ..., description="Feature type (e.g., 'agent', 'prompt', 'tool')"
    )
    feature_system_name: str = Field(
        ..., description="System name of the feature (e.g., 'DEMO_SALESFORCE_AGENT')"
    )
    feature_name: str = Field(
        ..., description="Human-readable feature name (e.g., 'Demo Salesforce Agent')"
    )
    feature_variant: Optional[str] = Field(
        None, description="Feature variant identifier (e.g., 'variant_4')"
    )

    # Trace and execution information
    trace_id: Optional[str] = Field(None, description="Associated trace identifier")
    status: str = Field(
        ..., description="Execution status (e.g., 'success', 'error', 'failure')"
    )

    # Source and channel information
    channel: Optional[str] = Field(
        None, description="Execution channel (e.g., 'production', 'development')"
    )
    source: Optional[str] = Field(
        None, description="Metric source (e.g., 'Runtime AI App', 'Web UI')"
    )

    # User and consumer information
    user_id: Optional[str] = Field(None, description="User identifier")
    consumer_name: Optional[str] = Field(
        None, description="Consumer name (e.g., 'DEMO_SALESFORCE_AGENT')"
    )
    consumer_type: Optional[str] = Field(
        None, description="Consumer type (e.g., 'agent', 'tool', 'prompt')"
    )

    # Timing information
    start_time: Optional[datetime] = Field(
        None, description="Metric execution start time"
    )
    end_time: Optional[datetime] = Field(None, description="Metric execution end time")
    latency: Optional[float] = Field(
        None, description="Execution latency in milliseconds"
    )

    # Conversation information
    conversation_id: Optional[str] = Field(
        None, description="Associated conversation identifier"
    )
    conversation_data: Optional[dict[str, Any]] = Field(
        None,
        description="Conversation metrics including tool call latency, topics, likes, dislikes, messages count",
    )

    # Cost tracking
    cost: Optional[float] = Field(None, description="Total execution cost")

    # Additional data
    extra_data: Optional[dict[str, Any]] = Field(
        None, description="Additional metric metadata and custom fields"
    )


# Mixin for update operations with all fields optional
class MetricUpdateFieldsMixin(BaseModel):
    """Mixin containing all Metric fields as optional for updates."""

    # Feature information
    feature_type: Optional[str] = Field(
        None, description="Feature type (e.g., 'agent', 'prompt', 'tool')"
    )
    feature_system_name: Optional[str] = Field(
        None, description="System name of the feature (e.g., 'DEMO_SALESFORCE_AGENT')"
    )
    feature_name: Optional[str] = Field(
        None, description="Human-readable feature name (e.g., 'Demo Salesforce Agent')"
    )
    feature_variant: Optional[str] = Field(
        None, description="Feature variant identifier (e.g., 'variant_4')"
    )

    # Trace and execution information
    trace_id: Optional[str] = Field(None, description="Associated trace identifier")
    status: Optional[str] = Field(
        None, description="Execution status (e.g., 'success', 'error', 'failure')"
    )

    # Source and channel information
    channel: Optional[str] = Field(
        None, description="Execution channel (e.g., 'production', 'development')"
    )
    source: Optional[str] = Field(
        None, description="Metric source (e.g., 'Runtime AI App', 'Web UI')"
    )

    # User and consumer information
    user_id: Optional[str] = Field(None, description="User identifier")
    consumer_name: Optional[str] = Field(
        None, description="Consumer name (e.g., 'DEMO_SALESFORCE_AGENT')"
    )
    consumer_type: Optional[str] = Field(
        None, description="Consumer type (e.g., 'agent', 'tool', 'prompt')"
    )

    # Timing information
    start_time: Optional[datetime] = Field(
        None, description="Metric execution start time"
    )
    end_time: Optional[datetime] = Field(None, description="Metric execution end time")
    latency: Optional[float] = Field(
        None, description="Execution latency in milliseconds"
    )

    # Conversation information
    conversation_id: Optional[str] = Field(
        None, description="Associated conversation identifier"
    )
    conversation_data: Optional[dict[str, Any]] = Field(
        None,
        description="Conversation metrics including tool call latency, topics, likes, dislikes, messages count",
    )

    # Cost tracking
    cost: Optional[float] = Field(None, description="Total execution cost")

    # Additional data
    extra_data: Optional[dict[str, Any]] = Field(
        None, description="Additional metric metadata and custom fields"
    )


# Pydantic schemas for Metrics
class Metric(BaseSchema, MetricFieldsMixin):
    """Metric schema for serialization."""


class MetricCreate(MetricFieldsMixin):
    """Schema for creating a new metric."""


class MetricUpdate(MetricUpdateFieldsMixin):
    """Schema for updating an existing metric."""
