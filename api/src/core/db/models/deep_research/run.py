"""Deep Research Run database model."""

from __future__ import annotations

from typing import Any, Optional

from advanced_alchemy.types import JsonB
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from ..base import UUIDv7AuditBase


class DeepResearchRun(UUIDv7AuditBase):
    """Deep Research Run entity.

    Inherits from UUIDv7AuditBase which provides:
    - id: UUID primary key
    - created_at, updated_at: Timestamps
    """

    __tablename__ = "deep_research_runs"

    # Optional client identifier
    client_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Optional client-side identifier",
        index=True,
    )

    # Run status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        comment="Run status: pending, running, completed, failed",
        index=True,
    )

    # Input data for the research (flexible JSONB)
    input: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB,
        nullable=True,
        comment="Input data for the research (e.g., {'query': 'research question'})",
    )

    # Config snapshot used for this run
    config: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB, nullable=True, comment="Configuration snapshot used for this run"
    )

    # Config system name snapshot for consistent display/traceability
    config_system_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="System name of the config used for this run",
        index=True,
    )

    # Run execution details stored as flexible JSONB for future adjustments
    # Expected structure: {memory: {}, iterations: [], result: {}, error: str}
    details: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB,
        nullable=True,
        comment="Run execution details in JSON format (progress, memory, iterations, result, error)",
    )
