"""Middleware that populates the audit context for HTTP requests.

Must run AFTER the auth middleware (so ``scope["auth"]`` is set) and AFTER
the request-id middleware (so the correlation id is available). Reads the
``Auth`` object once and builds an ``AuditContext`` that the SQLAlchemy
audit listener will read at flush time.

Unauthenticated requests get an ``ANONYMOUS`` context — they still write
audit rows if the handler happens to mutate an auditable entity (rare,
since such routes are usually `exclude_from_auth` reads).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from uuid import UUID

from litestar.enums import ScopeType
from litestar.middleware import AbstractMiddleware
from litestar.types import Receive, Scope, Send
from sqlalchemy import select

from core.audit import (
    ActorType,
    AuditContext,
    AuditSource,
    reset_audit_context,
    set_audit_context,
)

if TYPE_CHECKING:
    from middlewares.auth import Auth

logger = logging.getLogger(__name__)


def _coerce_uuid(value: object) -> UUID | None:
    if isinstance(value, UUID):
        return value
    if value is None:
        return None
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return None


_AI_REQUEST_HEADER = b"x-ai-request-id"


def _extract_ai_request_id(scope: Scope) -> UUID | None:
    """Pick up ``X-AI-Request-Id`` from the request headers.

    When the UI applies an AI suggestion and the user then saves, the
    save request carries this header so the audit row that records the
    save links back to the originating ai_edit_request.
    """
    for name, value in scope.get("headers", []) or []:
        if name == _AI_REQUEST_HEADER:
            raw = value.decode("latin-1") if isinstance(value, bytes) else str(value)
            return _coerce_uuid(raw)
    return None


def _build_context(scope: Scope) -> AuditContext:
    auth: "Auth | None" = scope.get("auth")
    state = scope.get("state") or {}
    request_id = state.get("request_id") if isinstance(state, dict) else None
    ai_request_id = _extract_ai_request_id(scope)

    if auth is None:
        return AuditContext(
            actor_type=ActorType.ANONYMOUS,
            actor_id=None,
            actor_display="anonymous",
            source=AuditSource.WEB_UI,
            request_id=request_id,
            tenant_id=None,
            ai_request_id=ai_request_id,
        )

    tenant_id = _coerce_uuid(auth.tenant_id)

    if auth.type == "api_key":
        client_code = (auth.data or {}).get("api_client_code") or auth.user_id or ""
        return AuditContext(
            actor_type=ActorType.API_KEY,
            actor_id=None,
            actor_display=f"api_key:{client_code}",
            source=AuditSource.API_KEY,
            request_id=request_id,
            tenant_id=tenant_id,
            ai_request_id=ai_request_id,
        )

    user_uuid = _coerce_uuid(auth.user_id)
    data = auth.data or {}
    display = (
        data.get("email")
        or data.get("preferred_username")
        or (auth.user.email if auth.user is not None else None)
        or (auth.user_id or "")
    )

    # When an AI request id is present the source is AI_ASSISTANT, so
    # audit history can filter "show only AI-driven saves".
    source = AuditSource.AI_ASSISTANT if ai_request_id else AuditSource.WEB_UI

    return AuditContext(
        actor_type=ActorType.USER,
        actor_id=user_uuid,
        actor_display=str(display),
        source=source,
        request_id=request_id,
        tenant_id=tenant_id,
        ai_request_id=ai_request_id,
    )


async def _validate_ai_request_id(ctx: AuditContext) -> AuditContext:
    if ctx.ai_request_id is None or ctx.tenant_id is None:
        return ctx
    try:
        from core.config.app import alchemy
        from core.db.models.ai_edit_request import AIEditRequest

        actor_filter = (
            [AIEditRequest.actor_id.is_(None)]
            if ctx.actor_id is None
            else [AIEditRequest.actor_id == ctx.actor_id]
        )

        async with alchemy.get_session() as session:
            row = (
                await session.execute(
                    select(AIEditRequest.id).where(
                        AIEditRequest.id == ctx.ai_request_id,
                        AIEditRequest.tenant_id == ctx.tenant_id,
                        AIEditRequest.status == "succeeded",
                        *actor_filter,
                    )
                )
            ).scalar_one_or_none()
        if row is not None:
            return ctx
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not validate AI request id: %r", exc)

    return AuditContext(
        actor_type=ctx.actor_type,
        actor_id=ctx.actor_id,
        actor_display=ctx.actor_display,
        source=AuditSource.WEB_UI,
        request_id=ctx.request_id,
        tenant_id=ctx.tenant_id,
        ai_request_id=None,
    )


class AuditContextMiddleware(AbstractMiddleware):
    """Set the per-request audit context from auth + request state."""

    scopes = {ScopeType.HTTP}

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        ctx = _build_context(scope)
        ctx = await _validate_ai_request_id(ctx)
        token = set_audit_context(ctx)
        try:
            await self.app(scope, receive, send)
        finally:
            reset_audit_context(token)
