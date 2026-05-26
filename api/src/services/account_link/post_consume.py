"""Per-channel post-consume hooks for account-link flow.

A hook runs inside the same transaction that creates the
``user_account_oauth`` row, so any cleanup it does (e.g. backfilling channel-
specific user state) is atomic with the binding itself.

Hooks are keyed by ``channel_kind`` (free-form string from the link-code
row — "teams", "slack", "discord", …). At most one hook per channel_kind;
registering twice overwrites. Channels with no hook just skip cleanly.
"""

from __future__ import annotations

from dataclasses import dataclass
from logging import getLogger
from typing import Any, Awaitable, Callable, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

logger = getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PostConsumeHookContext:
    """Everything a post-consume hook needs to know about a binding event."""

    provider: str
    subject_id: str
    channel_kind: Optional[str]
    channel_id: Optional[str]
    extra: Optional[dict[str, Any]]

    # The user we just bound the identity to.
    user_id: UUID
    user_tenant_id: UUID


PostConsumeHook = Callable[[PostConsumeHookContext, AsyncSession], Awaitable[None]]


_HOOKS: dict[str, PostConsumeHook] = {}


def register_post_consume_hook(channel_kind: str, hook: PostConsumeHook) -> None:
    """Register a post-consume hook for a given channel.

    Idempotent only in the sense that the last registration wins — call this
    once per channel, on module import of the channel's package.
    """
    if not channel_kind:
        raise ValueError("channel_kind must be a non-empty string")
    if channel_kind in _HOOKS and _HOOKS[channel_kind] is not hook:
        logger.warning(
            "Overwriting account-link post-consume hook for channel_kind=%s",
            channel_kind,
        )
    _HOOKS[channel_kind] = hook


async def run_post_consume_hook(
    ctx: PostConsumeHookContext, session: AsyncSession
) -> None:
    """Dispatch to the registered hook for ``ctx.channel_kind``, if any."""
    if not ctx.channel_kind:
        return
    hook = _HOOKS.get(ctx.channel_kind)
    if hook is None:
        return
    await hook(ctx, session)
