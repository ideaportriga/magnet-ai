"""
Metrics table definition.
"""

from __future__ import annotations

from typing import Optional

from advanced_alchemy.base import AdvancedDeclarativeBase, CommonTableAttributes
from advanced_alchemy.mixins import (
    AuditColumns,
)
from advanced_alchemy.types import DateTimeUTC, JsonB
from sqlalchemy import Float, String
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column


class Metric(CommonTableAttributes, AdvancedDeclarativeBase, AsyncAttrs, AuditColumns):
    """
    Metric entity for storing feature performance metrics and observability data.

    Based on the metric JSON structure with feature information, timing, conversation data, and cost tracking.
    """

    __tablename__ = "metrics"

    id: Mapped[str] = mapped_column(
        String(30),
        primary_key=True,
        comment="Unique identifier for the metric",
        index=True,
    )

    # Feature information
    feature_type: Mapped[str] = mapped_column(
        String(100),
        nullable=True,
        comment="Feature type (e.g., 'agent', 'prompt', 'tool')",
        index=True,
    )

    feature_system_name: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
        comment="System name of the feature (e.g., 'DEMO_SALESFORCE_AGENT')",
        index=True,
    )

    feature_name: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
        comment="Human-readable feature name (e.g., 'Demo Salesforce Agent')",
    )

    feature_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Unique identifier for the feature (e.g., 'agent_123')",
    )

    feature_variant: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Feature variant identifier (e.g., 'variant_4')",
        index=True,
    )

    # Trace and execution information
    trace_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Associated trace identifier",
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(100),
        nullable=True,
        comment="Execution status (e.g., 'success', 'error', 'failure')",
        index=True,
    )

    # Source and channel information
    channel: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Execution channel (e.g., 'production', 'development')",
        index=True,
    )

    source: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Metric source (e.g., 'Runtime AI App', 'Web UI')",
    )

    # User and consumer information
    user_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="User identifier",
        index=True,
    )

    consumer_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Consumer name (e.g., 'DEMO_SALESFORCE_AGENT')",
        index=True,
    )

    consumer_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Consumer type (e.g., 'agent', 'tool', 'prompt')",
        index=True,
    )

    # Timing information
    start_time: Mapped[Optional[DateTimeUTC]] = mapped_column(
        DateTimeUTC,
        nullable=True,
        comment="Metric execution start time",
        index=True,
    )

    end_time: Mapped[Optional[DateTimeUTC]] = mapped_column(
        DateTimeUTC,
        nullable=True,
        comment="Metric execution end time",
        index=True,
    )

    latency: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Execution latency in milliseconds",
        index=True,
    )

    # Conversation information
    conversation_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Associated conversation identifier",
        index=True,
    )

    conversation_data: Mapped[Optional[dict]] = mapped_column(
        JsonB,
        nullable=True,
        comment="Conversation metrics including tool call latency, topics, likes, dislikes, messages count",
    )

    # Cost tracking
    cost: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Total execution cost",
        index=True,
    )

    # Additional data
    extra_data: Mapped[Optional[dict]] = mapped_column(
        JsonB,
        nullable=True,
        comment="Additional metric metadata and custom fields",
    )

    # X-attributes for additional context (e.g., org-id)
    x_attributes: Mapped[Optional[dict]] = mapped_column(
        JsonB,
        nullable=True,
        comment="Additional context attributes (e.g., organization ID)",
    )

    def __repr__(self) -> str:
        return (
            f"<Metric(feature_type='{self.feature_type}', "
            f"feature_system_name='{self.feature_system_name}', "
            f"status='{self.status}')>"
        )
