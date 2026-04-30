from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from .status import JobStatus


class NoteTakerJobSchema(BaseModel):
    """Read schema for a preview job."""

    id: UUID
    settings_id: Optional[UUID] = None
    user_id: Optional[str] = None
    source_url: Optional[str] = None
    participants: Optional[list[str]] = None
    status: str = JobStatus.PENDING
    result: Optional[dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_validator("participants", mode="before")
    @classmethod
    def _parse_participants(cls, v: Any) -> Any:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return []
        return v

    @field_validator("result", mode="before")
    @classmethod
    def _parse_result(cls, v: Any) -> Any:
        # asyncpg returns JSONB columns as either a `dict` (when the JSONB
        # type codec is registered on the connection) or a raw JSON string
        # (when it isn't). Reads can land on either kind of connection
        # because the SQLAlchemy pool serves multiple code paths and only
        # `PgVectorClient._acquire` registers the codec. Parse the string
        # form here so the Pydantic dict expectation holds in both cases.
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return None
        return v


class NoteTakerJobCreate(BaseModel):
    """Schema for creating a new preview job."""

    settings_id: Optional[UUID] = None
    user_id: Optional[str] = None
    source_url: Optional[str] = None
    participants: list[str] = Field(default_factory=list)
    stt_model_system_name: Optional[str] = None
    status: str = JobStatus.PENDING


class NoteTakerJobUpdate(BaseModel):
    """Schema for updating a preview job."""

    status: Optional[str] = None
    result: Optional[dict[str, Any]] = None
