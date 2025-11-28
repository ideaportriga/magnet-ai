"""
Jobs table definition.
"""

from __future__ import annotations

from typing import Optional

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.types import DateTimeUTC, JsonB
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column


class Job(UUIDv7AuditBase):
    """
    Job entity for storing job configurations and execution information.

    Based on the job JSON structure with definition, status, and scheduling info.
    """

    __tablename__ = "jobs"

    # Job definition stored as JSONB
    definition: Mapped[Optional[dict]] = mapped_column(
        JsonB,
        nullable=True,
        comment="Job definition including configuration and parameters",
    )

    # Job status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Current job status (e.g., Configuration, Completed, Running)",
        index=True,
    )

    # Scheduling information
    next_run: Mapped[Optional[DateTimeUTC]] = mapped_column(
        DateTimeUTC, nullable=True, comment="Next scheduled run time"
    )

    last_run: Mapped[Optional[DateTimeUTC]] = mapped_column(
        DateTimeUTC, nullable=True, comment="Last execution time"
    )

    def __repr__(self) -> str:
        return f"<Job, status='{self.status}')>"
