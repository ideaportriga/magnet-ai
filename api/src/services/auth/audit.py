"""Login audit events.

Best-effort writer for authentication-related audit entries. Runs in its own
transaction so audit-write failures never block the login/logout flow.
"""

from __future__ import annotations

from logging import getLogger
from typing import Any, Mapping
from uuid import UUID

from core.config.app import alchemy
from services.access_control import write_audit_log

logger = getLogger(__name__)


async def record_login_event(
    *,
    tenant_id: UUID | str,
    user_id: UUID | str | None,
    action: str,
    payload: Mapping[str, Any] | None = None,
) -> None:
    """Append a login/logout entry to access_audit_log.

    Best-effort: any error here is logged and swallowed so authentication
    is never broken by audit-log failures.
    """
    try:
        async with alchemy.get_session() as session:
            await write_audit_log(
                session,
                tenant_id=tenant_id,
                actor_id=user_id,
                action=action,
                target_type="user",
                target_id=user_id,
                payload=dict(payload or {}),
            )
            await session.commit()
    except Exception:
        logger.exception(
            "Failed to record login audit event action=%s user_id=%s",
            action,
            user_id,
        )


def get_client_ip(request: Any) -> str | None:
    """Extract client IP from a Litestar request/connection.

    Honors X-Forwarded-For when running behind a reverse proxy.
    """
    try:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        client = request.scope.get("client") if hasattr(request, "scope") else None
        return client[0] if client else None
    except Exception:
        return None
