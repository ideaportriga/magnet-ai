"""Pydantic models for AI-edit requests and results."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AIEditStatus(StrEnum):
    SUCCEEDED = "succeeded"
    SCHEMA_INVALID = "schema_invalid"
    LLM_ERROR = "llm_error"


class AIEditUsage(BaseModel):
    """Token + cost accounting for a single AI-edit call."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    model: str | None = None


class AIEditResult(BaseModel):
    """Successful AI-edit result.

    ``new_state`` is the full entity state the LLM produced (after Pydantic
    validation + forbidden-path stripping). ``diff`` is the per-path diff vs
    the entity's current snapshot, in the same shape as ``EntityAuditLog.diff``
    so the same diff renderer works for both.
    """

    ai_request_id: UUID
    entity_type: str
    entity_id: UUID
    status: AIEditStatus = AIEditStatus.SUCCEEDED
    new_state: dict[str, Any]
    diff: dict[str, dict[str, Any]] = Field(default_factory=dict)
    usage: AIEditUsage = Field(default_factory=AIEditUsage)


class AIEditFailure(Exception):
    """Raised when an AI-edit call cannot produce a valid new state."""

    def __init__(
        self,
        *,
        status: AIEditStatus,
        message: str,
        usage: AIEditUsage | None = None,
        ai_request_id: UUID | None = None,
        details: Optional[dict[str, Any]] = None,
        snapshot_before: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.message = message
        self.usage = usage or AIEditUsage()
        self.ai_request_id = ai_request_id
        self.details = details or {}
        self.snapshot_before = snapshot_before
