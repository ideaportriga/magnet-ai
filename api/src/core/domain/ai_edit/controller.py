"""HTTP surface for the AI entity editor.

Endpoints:
  POST /ai-edit/{entity_type}/{entity_id}   — propose a new state
  GET  /ai-edit/history                     — list past requests
  GET  /ai-edit/history/{request_id}        — full snapshot+payload

Authorization model:
  * The caller must have ``AI_EDIT_EXECUTE`` (feature flag — turn off to
    disable the AI editor entirely for a tenant role) AND the entity's
    own write permission (so we never escalate edit capability).
  * History endpoints require ``AUDIT_READ`` (the AI request log is a
    sibling of the audit log).
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from litestar import Controller, Request, get, post
from litestar.exceptions import (
    HTTPException,
    NotFoundException,
    PermissionDeniedException,
    ValidationException,
)
from litestar.status_codes import HTTP_403_FORBIDDEN
from sqlalchemy import select

from core.config.app import alchemy
from core.db.models.ai_edit_request import AIEditRequest
from guards.permissions import (
    Permission,
    get_effective_permissions,
    require_permission,
)
from middlewares.auth import Auth
from services.ai_entity_editor import (
    AIEditFailure,
    AIEditUsage,
    AIEditableDescriptor,
    ai_edit_entity,
    get_ai_editable,
)
from services.ai_entity_editor.service import _build_snapshot
from services.access_control.permissions import PermissionService

from .schemas import (
    AIEditHistoryDetail,
    AIEditHistoryEntry,
    AIEditRequestBody,
    AIEditResponse,
    AIEditUsageDto,
)

logger = logging.getLogger(__name__)


def _require_auth(request: Request) -> Auth:
    auth: Auth | None = request.scope.get("auth")
    if auth is None or not auth.tenant_id:
        raise PermissionDeniedException("Tenant context required")
    return auth


def _require_uuid(value: str | None, name: str) -> UUID:
    if not value:
        raise PermissionDeniedException(f"{name} required")
    try:
        return UUID(str(value))
    except (TypeError, ValueError) as exc:
        raise PermissionDeniedException(f"Invalid {name}") from exc


def _check_entity_write_perm(*, auth: Auth, descriptor: AIEditableDescriptor) -> None:
    """Caller must hold the entity-specific WRITE permission in addition
    to AI_EDIT_EXECUTE — AI editing is a privileged write path, not a
    sneaky way to bypass per-entity write permissions."""
    effective = get_effective_permissions(auth)
    if descriptor.write_permission.value not in effective:
        raise PermissionDeniedException(
            f"Missing {descriptor.write_permission.value} permission"
        )


def _to_usage_dto(usage: AIEditUsage) -> AIEditUsageDto:
    return AIEditUsageDto(
        prompt_tokens=usage.prompt_tokens,
        completion_tokens=usage.completion_tokens,
        total_tokens=usage.total_tokens,
        cost_usd=float(usage.cost_usd),
        latency_ms=usage.latency_ms,
        model=usage.model,
    )


async def _persist_success(
    *,
    session,
    auth: Auth,
    entity_type: str,
    entity_id: UUID,
    tenant_id: UUID,
    instruction: str,
    snapshot_before: dict[str, Any],
    snapshot_after: dict[str, Any],
    usage: AIEditUsage,
) -> UUID:
    actor_id: UUID | None = None
    if auth.user_id:
        try:
            actor_id = UUID(str(auth.user_id))
        except (TypeError, ValueError):
            actor_id = None

    row = AIEditRequest(
        tenant_id=tenant_id,
        actor_id=actor_id,
        entity_type=entity_type,
        entity_id=entity_id,
        instruction=instruction,
        model=usage.model,
        status="succeeded",
        prompt_tokens=usage.prompt_tokens,
        completion_tokens=usage.completion_tokens,
        total_tokens=usage.total_tokens,
        cost_usd=usage.cost_usd,
        latency_ms=usage.latency_ms,
        snapshot_before=snapshot_before,
        snapshot_after=snapshot_after,
    )
    session.add(row)
    await session.flush()
    return row.id


async def _persist_failure(
    *,
    session,
    auth: Auth,
    entity_type: str,
    entity_id: UUID,
    tenant_id: UUID,
    instruction: str,
    error: AIEditFailure,
    snapshot_before: dict[str, Any] | None = None,
) -> UUID:
    actor_id: UUID | None = None
    if auth.user_id:
        try:
            actor_id = UUID(str(auth.user_id))
        except (TypeError, ValueError):
            actor_id = None

    row = AIEditRequest(
        tenant_id=tenant_id,
        actor_id=actor_id,
        entity_type=entity_type,
        entity_id=entity_id,
        instruction=instruction,
        model=error.usage.model,
        status=error.status.value,
        error_message=error.message,
        prompt_tokens=error.usage.prompt_tokens,
        completion_tokens=error.usage.completion_tokens,
        total_tokens=error.usage.total_tokens,
        cost_usd=error.usage.cost_usd,
        latency_ms=error.usage.latency_ms,
        snapshot_before=snapshot_before,
        snapshot_after=None,
    )
    session.add(row)
    await session.flush()
    return row.id


def _to_history_entry(row: AIEditRequest) -> AIEditHistoryEntry:
    return AIEditHistoryEntry(
        id=row.id,
        tenant_id=row.tenant_id,
        actor_id=row.actor_id,
        entity_type=row.entity_type,
        entity_id=row.entity_id,
        instruction=row.instruction,
        model=row.model,
        status=row.status,
        error_message=row.error_message,
        prompt_tokens=row.prompt_tokens or 0,
        completion_tokens=row.completion_tokens or 0,
        total_tokens=row.total_tokens or 0,
        cost_usd=float(row.cost_usd or 0),
        latency_ms=row.latency_ms or 0,
        created_at=row.created_at,
    )


class AIEditController(Controller):
    path = "/ai-edit"
    tags = ["Admin / AI Edit"]

    @post(
        "/{entity_type:str}/{entity_id:uuid}",
        summary="Propose a new entity state from a natural-language instruction",
        guards=[require_permission(Permission.AI_EDIT_EXECUTE)],
    )
    async def propose_endpoint(
        self,
        request: Request,
        entity_type: str,
        entity_id: UUID,
        data: AIEditRequestBody,
    ) -> AIEditResponse:
        auth = _require_auth(request)
        tenant_id = _require_uuid(auth.tenant_id, "tenant_id")

        descriptor = get_ai_editable(entity_type)
        if descriptor is None:
            raise NotFoundException(
                f"Entity type '{entity_type}' is not registered for AI editing"
            )

        _check_entity_write_perm(auth=auth, descriptor=descriptor)

        async with alchemy.get_session() as session:
            entity = await session.get(descriptor.model, entity_id)
            entity_tenant_id = (
                getattr(entity, "tenant_id", None) if entity is not None else None
            )
            if entity is None or (
                entity_tenant_id is not None and entity_tenant_id != tenant_id
            ):
                raise NotFoundException("Entity not found")
            if not await PermissionService.can(
                session,
                auth=auth,
                action="edit",
                resource_type=descriptor.resource_type,
                resource=entity,
            ):
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN,
                    detail="You don't have permission to edit this entity",
                )

            async def on_persist(*, descriptor, **kwargs):
                # The service passes `descriptor` plus entity_id/tenant_id/
                # instruction/snapshot_before/snapshot_after/usage. Pull
                # `entity_type` from the descriptor and drop the rest of
                # the descriptor object — `_persist_success` only stores
                # primitives, not the dataclass.
                return await _persist_success(
                    session=session,
                    auth=auth,
                    entity_type=descriptor.entity_type,
                    **kwargs,
                )

            try:
                result = await ai_edit_entity(
                    session,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    tenant_id=tenant_id,
                    instruction=data.instruction,
                    model_system_name=data.model,
                    on_persist=on_persist,
                )
            except AIEditFailure as failure:
                if failure.snapshot_before is None:
                    try:
                        failure.snapshot_before = _build_snapshot(entity, descriptor)
                    except Exception:  # noqa: BLE001
                        pass
                # Persist failure row separately so we still have an audit
                # trail for billing + prompt-eval purposes.
                try:
                    await _persist_failure(
                        session=session,
                        auth=auth,
                        entity_type=entity_type,
                        entity_id=entity_id,
                        tenant_id=tenant_id,
                        instruction=data.instruction,
                        error=failure,
                        snapshot_before=getattr(failure, "snapshot_before", None),
                    )
                    await session.commit()
                except Exception as persist_exc:  # noqa: BLE001
                    # Avoid logger.exception — structlog's JSON serializer
                    # can choke on exc_info contents (see service.py for
                    # the same workaround).
                    logger.error(
                        "Failed to persist AI-edit failure row: %r", persist_exc
                    )
                # Surface a 422 for any predictable failure (validation,
                # llm-protocol errors). We deliberately don't 500 — these
                # are user-facing outcomes, not server bugs.
                raise ValidationException(failure.message) from failure

            await session.commit()

        return AIEditResponse(
            ai_request_id=result.ai_request_id,
            entity_type=result.entity_type,
            entity_id=result.entity_id,
            status=result.status.value,
            new_state=result.new_state,
            diff=result.diff,
            usage=_to_usage_dto(result.usage),
        )

    # ── History ─────────────────────────────────────────────────────

    @get(
        "/history",
        summary="List recent AI-edit requests for the caller's tenant",
        guards=[require_permission(Permission.AUDIT_READ)],
    )
    async def list_history(
        self,
        request: Request,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        actor_id: Optional[UUID] = None,
        status: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AIEditHistoryEntry]:
        auth = _require_auth(request)
        tenant_id = _require_uuid(auth.tenant_id, "tenant_id")

        limit = max(1, min(int(limit), 500))
        offset = max(0, int(offset))

        async with alchemy.get_session() as session:
            stmt = (
                select(AIEditRequest)
                .where(AIEditRequest.tenant_id == tenant_id)
                .order_by(AIEditRequest.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            if entity_type:
                stmt = stmt.where(AIEditRequest.entity_type == entity_type)
            if entity_id:
                stmt = stmt.where(AIEditRequest.entity_id == entity_id)
            if actor_id:
                stmt = stmt.where(AIEditRequest.actor_id == actor_id)
            if status:
                stmt = stmt.where(AIEditRequest.status == status)
            if date_from:
                stmt = stmt.where(AIEditRequest.created_at >= date_from)
            if date_to:
                stmt = stmt.where(AIEditRequest.created_at <= date_to)

            rows = (await session.execute(stmt)).scalars().all()

        return [_to_history_entry(r) for r in rows]

    @get(
        "/history/{request_id:uuid}",
        summary="Full AI-edit request with snapshot_before/after",
        guards=[require_permission(Permission.AUDIT_READ)],
    )
    async def get_history_detail(
        self,
        request: Request,
        request_id: UUID,
    ) -> AIEditHistoryDetail:
        auth = _require_auth(request)
        tenant_id = _require_uuid(auth.tenant_id, "tenant_id")

        async with alchemy.get_session() as session:
            row = (
                await session.execute(
                    select(AIEditRequest).where(
                        AIEditRequest.id == request_id,
                        AIEditRequest.tenant_id == tenant_id,
                    )
                )
            ).scalar_one_or_none()
        if row is None:
            raise NotFoundException("AI-edit request not found")

        entry = _to_history_entry(row)
        return AIEditHistoryDetail(
            **entry.model_dump(),
            snapshot_before=row.snapshot_before,
            snapshot_after=row.snapshot_after,
        )
