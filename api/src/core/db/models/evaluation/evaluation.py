from __future__ import annotations

from typing import Any, Optional

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.types import DateTimeUTC, JsonB
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column


class Evaluation(UUIDv7AuditBase):
    """Evaluation jobs table for tracking evaluation runs."""

    __tablename__ = "evaluations"

    # Job specific fields
    job_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Job identifier"
    )
    type: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Evaluation type"
    )
    test_sets: Mapped[Optional[list[str]]] = mapped_column(
        JsonB, nullable=True, comment="List of test sets used in evaluation"
    )
    started_at: Mapped[Optional[DateTimeUTC]] = mapped_column(
        DateTimeUTC(timezone=True), nullable=True, comment="Evaluation start time"
    )
    finished_at: Mapped[Optional[DateTimeUTC]] = mapped_column(
        DateTimeUTC(timezone=True), nullable=True, comment="Evaluation finish time"
    )
    status: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Evaluation status"
    )
    errors: Mapped[Optional[list[str]]] = mapped_column(
        JsonB, nullable=True, comment="Error details if any"
    )
    tool: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JsonB, nullable=True, comment="Tool configuration used"
    )
    results: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(
        JsonB,
        nullable=True,
        comment="Evaluation results with latency, score, usage data",
    )
