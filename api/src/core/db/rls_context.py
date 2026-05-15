"""
Row-level security context propagation.

PR 7 of `docs/access-control-tenancy-plan-v2_ai-claude.md`.

The contract:

  Python contextvars (`current_tenant_id`, `current_user_id`) carry the
  identity for the current logical request / job / unit of work. The
  SQLAlchemy `after_begin` event reads them and emits `SET LOCAL` so that
  Postgres RLS policies on tenant-scoped tables (`agents` first, more in
  later PRs) can `USING (tenant_id = current_setting('app.tenant_id'))`.

Why GUC and not a per-query parameter:

  - Application code that forgets `.where(tenant_id=...)` is still safe.
  - RLS runs at the planner level, not the ORM, so raw SQL is also covered.
  - `SET LOCAL` is scoped to the surrounding transaction — leaks between
    requests sharing a connection from the pool are impossible.

Anti-leak:

  - If a contextvar is unset (background job that didn't propagate, internal
    script), we set the GUC to the empty string. The policy then matches no
    rows, so a forgotten propagation fails closed rather than open.
  - `SET LOCAL` cannot persist past the transaction. Connection pool reuse
    is safe.

This module also exposes ``rls_context_scope(...)`` — a contextmanager that
sets the vars and resets them on exit. Useful in worker callbacks and admin
scripts that operate on behalf of a specific tenant.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator, Optional

from sqlalchemy import event, inspect, text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# Contextvars carry the identity for the current logical request. They
# propagate naturally across `await` boundaries because asyncio task tree
# inherits the parent context.
current_tenant_id: ContextVar[Optional[str]] = ContextVar(
    "current_tenant_id", default=None
)
current_user_id: ContextVar[Optional[str]] = ContextVar("current_user_id", default=None)


def set_rls_context(
    *,
    tenant_id: Optional[str],
    user_id: Optional[str] = None,
) -> tuple[object, object]:
    """Set the RLS contextvars. Returns the tokens needed to reset them."""
    t_token = current_tenant_id.set(str(tenant_id) if tenant_id else None)
    u_token = current_user_id.set(str(user_id) if user_id else None)
    return t_token, u_token


def reset_rls_context(tokens: tuple[object, object]) -> None:
    """Reset contextvars to their previous values."""
    t_token, u_token = tokens
    current_tenant_id.reset(t_token)
    current_user_id.reset(u_token)


async def apply_session_rls(session, *, tenant_id: Optional[str]) -> None:
    """Force `SET LOCAL app.tenant_id = ...` on an open session.

    `SET LOCAL` fires automatically at transaction-begin via the SQLAlchemy
    listener, so production code rarely needs this. It's useful inside long-
    running tests or workers that want to switch tenant identity mid-flight
    without committing the outer transaction. Caller is responsible for
    keeping the contextvar consistent.
    """
    value = str(tenant_id) if tenant_id else ""
    await session.execute(text(f"SET LOCAL app.tenant_id = '{value}'"))


@contextmanager
def rls_context_scope(
    *,
    tenant_id: Optional[str],
    user_id: Optional[str] = None,
) -> Iterator[None]:
    """Scope an RLS identity to a block of code (workers, scripts, tests).

    Example:
        with rls_context_scope(tenant_id=str(tenant.id)):
            await some_query()
    """
    tokens = set_rls_context(tenant_id=tenant_id, user_id=user_id)
    try:
        yield
    finally:
        reset_rls_context(tokens)


# ---------------------------------------------------------------------------
# SQLAlchemy event listener — applies GUC on every transaction
# ---------------------------------------------------------------------------


_LISTENER_INSTALLED = False


def install_session_guc_listener() -> None:
    """Register the global `after_begin` event listener.

    Idempotent — only one listener is ever installed even if called from
    multiple places (engine factory, tests, scripts).
    """
    global _LISTENER_INSTALLED
    if _LISTENER_INSTALLED:
        return

    @event.listens_for(Session, "after_begin")
    def _emit_set_local(session, transaction, connection):  # noqa: ANN001
        tenant_id = current_tenant_id.get() or ""
        user_id = current_user_id.get() or ""
        # `SET LOCAL` requires being inside a transaction (we are, by
        # definition — this is `after_begin`). Postgres-only syntax.
        try:
            connection.execute(text(f"SET LOCAL app.tenant_id = '{tenant_id}'"))
            connection.execute(text(f"SET LOCAL app.user_id = '{user_id}'"))
        except Exception:  # pragma: no cover
            # Non-Postgres backends (e.g. SQLite in some scripts) just no-op
            # — RLS isn't enforced there anyway. Log once at debug level so
            # a misconfiguration shows up.
            logger.debug("RLS GUC emit skipped (non-Postgres or no permission)")

    @event.listens_for(Session, "before_flush")
    def _populate_tenant_id(session, flush_context, instances):  # noqa: ANN001
        # Safety net: controllers force tenant_id via `force_create_fields`,
        # but raw `service.create({...})` and bulk callers may forget it.
        # Only fills *unset* attributes — explicit `tenant_id=None` is left
        # alone so NOT NULL/RLS checks still catch missing-tenant bugs.
        ctx_tenant = current_tenant_id.get()
        if not ctx_tenant:
            return
        for obj in session.new:
            mapper = getattr(obj, "__mapper__", None)
            if mapper is None or "tenant_id" not in mapper.columns:
                continue
            state = inspect(obj)
            attr = state.attrs.get("tenant_id")
            if attr is None:
                continue
            if attr.history.has_changes():
                continue
            obj.tenant_id = ctx_tenant

    _LISTENER_INSTALLED = True


# Install on import. This is safe because the function is idempotent and the
# event hook is purely a dispatch — it does nothing until a session actually
# begins a transaction.
install_session_guc_listener()
