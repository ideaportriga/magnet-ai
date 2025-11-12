"""
Traces table definition.
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


class Trace(CommonTableAttributes, AdvancedDeclarativeBase, AsyncAttrs, AuditColumns):
    """
    Trace entity for storing trace execution information and observability data.

    Based on the trace JSON structure with spans, cost details, and performance metrics.
    """

    __tablename__ = "traces"

    id: Mapped[str] = mapped_column(
        String(30),
        primary_key=True,
        comment="Unique identifier for the trace",
        index=True,
    )

    # Core trace information
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Trace name (e.g., 'NPS Feedback Summary')",
        index=True,
    )

    type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Trace type (e.g., 'prompt-template', 'chat', 'span')",
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Trace execution status (e.g., 'success', 'error', 'running')",
        index=True,
    )

    # Source and channel information
    channel: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Execution channel (e.g., 'production', 'development')",
        index=True,
    )

    source: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Trace source (e.g., 'Runtime API', 'Web UI')",
    )

    # User information
    user_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="User or API key identifier",
        index=True,
    )

    # Timing information
    start_time: Mapped[Optional[DateTimeUTC]] = mapped_column(
        DateTimeUTC,
        nullable=True,
        comment="Trace execution start time",
        index=True,
    )

    end_time: Mapped[Optional[DateTimeUTC]] = mapped_column(
        DateTimeUTC,
        nullable=True,
        comment="Trace execution end time",
        index=True,
    )

    latency: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Execution latency in milliseconds",
        index=True,
    )

    # Cost tracking
    cost_details: Mapped[Optional[dict]] = mapped_column(
        JsonB,
        nullable=True,
        comment="Cost breakdown including chat, embed, rerank, and total costs",
    )

    # Additional data
    extra_data: Mapped[Optional[dict]] = mapped_column(
        JsonB,
        nullable=True,
        comment="Additional trace metadata and custom fields",
    )

    # Spans data - nested trace information
    spans: Mapped[Optional[list[dict]]] = mapped_column(
        JsonB,
        nullable=True,
        comment="List of trace spans with detailed execution information",
    )

    def __repr__(self) -> str:
        return (
            f"<Trace(name='{self.name}', type='{self.type}', status='{self.status}')>"
        )
