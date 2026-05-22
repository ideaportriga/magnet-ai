"""Tenant / RLS context propagation: API process → worker process.

The API process enqueues a task while handling an HTTP request — its
`current_tenant_id` / `current_user_id` / `current_is_superuser`
contextvars are set by the auth middleware. The worker is a separate
process, so those contextvars don't travel automatically.

This middleware serialises the tenant identity into the broker message
labels on `pre_send`, and restores it via `set_rls_context` on
`pre_execute`. `post_execute` (and `on_error`) resets the context so
worker tasks don't leak identity across executions.

Without this middleware:
  - `_populate_tenant_id` listener has no contextvar to pull from → new
    rows get `tenant_id=NULL`, which violates NOT NULL constraints on
    tenant-scoped tables.
  - RLS policies see empty GUC → fail-closed (zero rows visible), so
    tasks that read tenant-scoped data either see nothing or trip RLS.

Mirrors the pattern of `TraceContextMiddleware` (W3C trace context).
"""

from __future__ import annotations

from logging import getLogger
from typing import Any

from taskiq import TaskiqMessage, TaskiqMiddleware, TaskiqResult

from core.db.rls_context import reset_rls_context, set_rls_context
from core.db.rls_context import (
    current_is_superuser,
    current_tenant_id,
    current_user_id,
)

logger = getLogger(__name__)


# Label keys on the broker message.
_TENANT_LABEL = "mai_tenant_id"
_USER_LABEL = "mai_user_id"
_SUPERUSER_LABEL = "mai_is_superuser"

# Stash the reset-tokens on the message so post_execute can unwind.
_RLS_TOKENS_ATTR = "_mai_rls_tokens"


class TenantContextMiddleware(TaskiqMiddleware):
    """Carry tenant / user / is_superuser across the API → worker boundary."""

    async def pre_send(self, message: TaskiqMessage) -> TaskiqMessage:
        try:
            tenant = current_tenant_id.get()
            user = current_user_id.get()
            is_su = current_is_superuser.get()
            if tenant:
                message.labels[_TENANT_LABEL] = str(tenant)
            if user:
                message.labels[_USER_LABEL] = str(user)
            if is_su:
                message.labels[_SUPERUSER_LABEL] = "true"
        except Exception as exc:  # noqa: BLE001
            logger.debug("pre_send tenant inject failed: %s", exc)
        return message

    async def pre_execute(self, message: TaskiqMessage) -> TaskiqMessage:
        tenant = message.labels.get(_TENANT_LABEL)
        user = message.labels.get(_USER_LABEL)
        is_su = message.labels.get(_SUPERUSER_LABEL) == "true"
        # System tasks (cron, housekeeping) enqueue without any tenant — that
        # is fine, the GUC stays empty and the worker behaves like a system
        # actor (Q-3 / Q-4 nullable-policy semantics).
        if not tenant and not user and not is_su:
            return message
        try:
            tokens = set_rls_context(
                tenant_id=tenant,
                user_id=user,
                is_superuser=is_su,
            )
            setattr(message, _RLS_TOKENS_ATTR, tokens)
        except Exception as exc:  # noqa: BLE001
            logger.warning("pre_execute RLS set failed: %s", exc)
        return message

    async def post_execute(
        self, message: TaskiqMessage, result: TaskiqResult[Any]
    ) -> None:
        await self._reset(message)

    async def on_error(
        self,
        message: TaskiqMessage,
        result: TaskiqResult[Any],
        exception: BaseException,
    ) -> None:
        await self._reset(message)

    @staticmethod
    async def _reset(message: TaskiqMessage) -> None:
        tokens = getattr(message, _RLS_TOKENS_ATTR, None)
        if tokens is None:
            return
        try:
            reset_rls_context(tokens)
        except Exception as exc:  # noqa: BLE001
            logger.debug("RLS context reset failed: %s", exc)
