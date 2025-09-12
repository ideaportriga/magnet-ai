"""
Pydantic schemas for Jobs validation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from core.domain.base.schemas import (
    BaseSchema,
)


# Base mixin for common Job fields
class JobFieldsMixin(BaseModel):
    """Mixin containing all common Job fields."""

    # Job definition stored as JSON
    definition: Optional[dict] = Field(
        None, description="Job definition including configuration and parameters"
    )

    # Job status
    status: str = Field(
        ...,
        description="Current job status (e.g., Configuration, Completed, Running)",
        max_length=50,
    )

    # Scheduling information
    next_run: Optional[datetime] = Field(None, description="Next scheduled run time")

    last_run: Optional[datetime] = Field(None, description="Last execution time")


# Mixin for update operations with all fields optional
class JobUpdateFieldsMixin(BaseModel):
    """Mixin containing all Job fields as optional for updates."""

    # Job definition stored as JSON
    definition: Optional[dict] = Field(
        None, description="Job definition including configuration and parameters"
    )

    # Job status
    status: Optional[str] = Field(
        None,
        description="Current job status (e.g., Configuration, Completed, Running)",
        max_length=50,
    )

    # Scheduling information
    next_run: Optional[datetime] = Field(None, description="Next scheduled run time")

    last_run: Optional[datetime] = Field(None, description="Last execution time")


# Pydantic schemas for Jobs
class Job(BaseSchema, JobFieldsMixin):
    """Job schema for serialization."""


class JobCreate(JobFieldsMixin):
    """Schema for creating a new Job."""


class JobUpdate(JobUpdateFieldsMixin):
    """Schema for updating an existing Job."""
