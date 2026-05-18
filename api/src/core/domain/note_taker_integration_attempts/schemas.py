from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel


class NoteTakerIntegrationAttemptSchema(BaseModel):
    """Read schema for one `note_taker_integration_attempt` row."""

    id: UUID
    job_id: str
    integration_kind: str
    status: str
    attempt_count: int
    error_class: Optional[str] = None
    error: Optional[str] = None
    trace_id: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None
    retry_payload: Optional[dict[str, Any]] = None


class IntegrationAttemptRetryResponse(BaseModel):
    """Response from POST /{id}/retry."""

    id: UUID
    integration_kind: str
    job_id: str
    next_retry_at: Optional[datetime] = None
    immediately_requeued: bool = False
