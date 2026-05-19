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


def _build_context(scope: Scope) -> AuditContext:
    auth: "Auth | None" = scope.get("auth")
    state = scope.get("state") or {}
    request_id = state.get("request_id") if isinstance(state, dict) else None

    if auth is None:
        return AuditContext(
            actor_type=ActorType.ANONYMOUS,
            actor_id=None,
            actor_display="anonymous",
            source=AuditSource.WEB_UI,
            request_id=request_id,
            tenant_id=None,
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
        )

    user_uuid = _coerce_uuid(auth.user_id)
    data = auth.data or {}
    display = (
        data.get("email")
        or data.get("preferred_username")
        or (auth.user.email if auth.user is not None else None)
        or (auth.user_id or "")
    )

    return AuditContext(
        actor_type=ActorType.USER,
        actor_id=user_uuid,
        actor_display=str(display),
        source=AuditSource.WEB_UI,
        request_id=request_id,
        tenant_id=tenant_id,
    )


class AuditContextMiddleware(AbstractMiddleware):
    """Set the per-request audit context from auth + request state."""

    scopes = {ScopeType.HTTP}

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        ctx = _build_context(scope)
        token = set_audit_context(ctx)
        try:
            await self.app(scope, receive, send)
        finally:
            reset_audit_context(token)
