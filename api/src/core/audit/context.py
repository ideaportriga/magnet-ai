"""Audit context — who performed the current unit of work, and how.

Set from middleware for HTTP requests; from job/wrapper code for scheduler
and background tasks. The SQLAlchemy listener (see ``listener.py``) reads
this contextvar at flush time and stamps every audit row.

A missing context falls back to ``system_audit_context()`` so audit is
written even when the propagation path forgot to set it — it's safer to
log "system" than to drop the row.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass
from enum import StrEnum
from typing import Iterator, Optional
from uuid import UUID


class ActorType(StrEnum):
    USER = "user"
    API_KEY = "api_key"
    SCHEDULER = "scheduler"
    SYSTEM = "system"
    BACKGROUND = "background"
    ANONYMOUS = "anonymous"


class AuditSource(StrEnum):
    WEB_UI = "web_ui"
    API_KEY = "api_key"
    SCHEDULER = "scheduler"
    SYSTEM = "system"
    MIGRATION = "migration"
    AI_ASSISTANT = "ai_assistant"


@dataclass(frozen=True, slots=True)
class AuditContext:
    actor_type: ActorType
    actor_id: Optional[UUID] = None
    actor_display: str = ""
    source: AuditSource = AuditSource.SYSTEM
    request_id: Optional[str] = None
    tenant_id: Optional[UUID] = None


current_audit_context: ContextVar[Optional[AuditContext]] = ContextVar(
    "current_audit_context", default=None
)


def set_audit_context(ctx: AuditContext) -> Token:
    """Install ``ctx`` as the current audit context. Returns a reset token."""
    return current_audit_context.set(ctx)


def reset_audit_context(token: Token) -> None:
    current_audit_context.reset(token)


def system_audit_context(
    *,
    source: AuditSource = AuditSource.SYSTEM,
    display: str = "system",
    tenant_id: Optional[UUID] = None,
) -> AuditContext:
    """Fallback context for code paths that didn't propagate identity.

    Used by the listener when ``current_audit_context.get()`` is ``None``
    so an audit row is still written. The ``actor_id`` is ``None`` — pair
    with a meaningful ``display`` (e.g. ``'scheduler:cleanup_refresh_tokens'``)
    when calling from a known background path.
    """
    return AuditContext(
        actor_type=ActorType.SYSTEM,
        actor_id=None,
        actor_display=display,
        source=source,
        tenant_id=tenant_id,
    )


@contextmanager
def audit_context_scope(ctx: AuditContext) -> Iterator[None]:
    """Scope an audit context to a block of code (workers, scripts, tests).

    Example:
        with audit_context_scope(AuditContext(actor_type=ActorType.SCHEDULER, ...)):
            await do_work()
    """
    token = set_audit_context(ctx)
    try:
        yield
    finally:
        reset_audit_context(token)
