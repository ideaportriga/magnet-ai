from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class NoteTakerJobSchema(BaseModel):
    """Read schema for a preview job."""

    id: UUID
    settings_id: Optional[UUID] = None
    user_id: Optional[str] = None
    source_url: Optional[str] = None
    participants: Optional[list[str]] = None
    status: str = "pending"
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


class NoteTakerJobCreate(BaseModel):
    """Schema for creating a new preview job."""

    settings_id: Optional[UUID] = None
    user_id: Optional[str] = None
    source_url: Optional[str] = None
    participants: list[str] = Field(default_factory=list)
    stt_model_system_name: Optional[str] = None
    status: str = "pending"


class NoteTakerJobUpdate(BaseModel):
    """Schema for updating a preview job."""

    status: Optional[str] = None
    result: Optional[dict[str, Any]] = None
