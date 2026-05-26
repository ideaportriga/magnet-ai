"""Resolve Teams sender (AAD object id) to an internal (user_id, tenant_id).

The Bot Framework activity carries Azure AD identifiers
(`from_property.aad_object_id`, `channel_data.tenant.id`) but our RLS policies
need the *internal* tenant UUID and user UUID. This module bridges that gap by
looking up `user_account_oauth` for the Microsoft Entra provider.

If the AAD oid has no matching row, the user is "unlinked": we surface a
`teams_user` placeholder (so an admin can bind it from the admin UI) and the
caller refuses the turn. There is no auto-provisioning here — provisioning is
an explicit admin action.
"""

from __future__ import annotations

from dataclasses import dataclass
from logging import getLogger

from sqlalchemy import select

from microsoft_agents.hosting.core import TurnContext

from core.db.rls_context import rls_context_scope
from core.db.session import async_session_maker

logger = getLogger(__name__)

# Matches `provider_registry.py` and `oauth_name` writes in
# `identity_resolution.py:162` — keep this in sync if the OIDC strategy is
# ever renamed.
MICROSOFT_OAUTH_NAME = "microsoft"


@dataclass(frozen=True, slots=True)
class ResolvedIdentity:
    user_id: str
    tenant_id: str


def extract_aad_object_id(context: TurnContext) -> str | None:
    """Pull `aad_object_id` off the activity sender, if present."""
    activity = getattr(context, "activity", None)
    if not activity:
        return None
    from_user = getattr(activity, "from_property", None) or getattr(
        activity, "from", None
    )
    if not from_user:
        return None
    value = getattr(from_user, "aad_object_id", None)
    return str(value) if value else None


async def resolve_teams_user_identity(
    context: TurnContext,
) -> ResolvedIdentity | None:
    """Map the Teams sender's AAD oid → internal (user_id, tenant_id).

    Returns None when no `user_account_oauth` row matches — the caller should
    treat that as "unlinked" and refuse the turn.

    The lookup runs under a superuser RLS scope because the resolver does not
    yet know which tenant to scope to.
    """
    aad_oid = extract_aad_object_id(context)
    if not aad_oid:
        return None

    # Lazy imports — this module is loaded at adapter-build time, well before
    # the SQLAlchemy mappers are guaranteed configured.
    from core.db.models.user.user import User
    from core.db.models.user.user_oauth_account import UserOAuthAccount

    try:
        with rls_context_scope(tenant_id=None, is_superuser=True):
            async with async_session_maker() as session:
                stmt = (
                    select(User.id, User.tenant_id)
                    .join(UserOAuthAccount, UserOAuthAccount.user_id == User.id)
                    .where(
                        UserOAuthAccount.oauth_name == MICROSOFT_OAUTH_NAME,
                        UserOAuthAccount.account_id == aad_oid,
                        User.is_active.is_(True),
                    )
                    .limit(1)
                )
                row = (await session.execute(stmt)).first()
    except Exception:
        logger.exception(
            "Failed to resolve Teams identity for aad_object_id=%s", aad_oid
        )
        return None

    if row is None:
        return None
    user_id, tenant_id = row
    return ResolvedIdentity(user_id=str(user_id), tenant_id=str(tenant_id))
