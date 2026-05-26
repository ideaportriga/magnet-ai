"""Teams-side hook for the generic account-link consume flow.

When an ``AccountLinkCode`` with ``channel_kind == "teams"`` is consumed, we
also want to back-fill ``teams_user.tenant_id`` so any pre-existing
placeholder rows (written by the identity middleware while the user was
unlinked) become tenant-scoped immediately. This module registers the hook
on import — :mod:`services.agents.teams.note_taker` does ``import .teams_link_post_consume``
at module load so the registration happens before the first ``/link``
consume request.
"""

from __future__ import annotations

from logging import getLogger

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models.teams import TeamsUser
from services.account_link import (
    PostConsumeHookContext,
    register_post_consume_hook,
)

logger = getLogger(__name__)

TEAMS_CHANNEL_KIND = "teams"


async def _teams_post_consume(
    ctx: PostConsumeHookContext, session: AsyncSession
) -> None:
    """Backfill ``teams_user.tenant_id`` for every row that shares the AAD oid.

    Runs in the same transaction as the OAuth-link insert (see
    :func:`services.account_link.service.consume_link_code`), so the binding
    and the tenant-id backfill commit together.
    """
    result = await session.execute(
        update(TeamsUser)
        .where(TeamsUser.aad_object_id == ctx.subject_id)
        .values(tenant_id=ctx.user_tenant_id)
    )
    logger.info(
        "[account-link][teams] backfilled teams_user.tenant_id for "
        "aad_oid=%s user_id=%s (%d rows updated)",
        ctx.subject_id,
        ctx.user_id,
        getattr(result, "rowcount", 0) or 0,
    )


register_post_consume_hook(TEAMS_CHANNEL_KIND, _teams_post_consume)
