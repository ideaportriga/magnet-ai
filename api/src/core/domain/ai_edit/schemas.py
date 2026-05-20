"""Pydantic schemas for the AI-edit HTTP layer."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AIEditRequestBody(BaseModel):
    """Request body for ``POST /ai-edit/{entity_type}/{entity_id}``."""

    instruction: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Natural-language description of the change to make.",
    )
    model: Optional[str] = Field(
        default=None,
        description=(
            "system_name of the LLM model to use. NULL falls back to the "
            "tenant default model for the entity type."
        ),
    )


class AIEditUsageDto(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    model: Optional[str] = None


class AIEditResponse(BaseModel):
    """Response for a successful ``ai_edit`` call.

    The new state is returned in full so the client can drop it into the
    editBuffer.draft. The diff is the same shape as
    ``EntityAuditLogEntry.diff`` so the existing diff renderer works as-is.
    """

    ai_request_id: UUID
    entity_type: str
    entity_id: UUID
    status: str = "succeeded"
    new_state: dict[str, Any]
    diff: dict[str, dict[str, Any]] = Field(default_factory=dict)
    usage: AIEditUsageDto


# ── History endpoint shapes ────────────────────────────────────────


class AIEditHistoryEntry(BaseModel):
    id: UUID
    tenant_id: UUID
    actor_id: Optional[UUID] = None
    entity_type: str
    entity_id: UUID
    instruction: str
    model: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    created_at: datetime


class AIEditHistoryDetail(AIEditHistoryEntry):
    snapshot_before: Optional[dict[str, Any]] = None
    snapshot_after: Optional[dict[str, Any]] = None


def _decimal_to_float(value: Decimal | float | int | None) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)
