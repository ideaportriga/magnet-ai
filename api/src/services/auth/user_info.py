"""
Helper to build user info response from internal User object.

Used by /api/v2/auth/me to avoid code duplication.
"""

from __future__ import annotations

from logging import getLogger

from core.db.models.user.user import User
from middlewares.auth import Auth

logger = getLogger(__name__)


async def build_user_info(user: User, auth: Auth) -> dict:
    """Build a user info dict from a User object and Auth context."""
    roles = []
    try:
        roles = [r.slug for r in (user.roles or [])]
    except Exception:
        logger.warning("Failed to load roles for user %s", user.id, exc_info=True)

    oauth_accounts = await _load_oauth_accounts(user.id)

    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "avatar_url": user.avatar_url,
        "is_verified": user.is_verified,
        "is_superuser": user.is_superuser,
        "is_two_factor_enabled": user.is_two_factor_enabled,
        "roles": roles,
        "auth_method": auth.type,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "oauth_accounts": oauth_accounts,
    }


async def _load_oauth_accounts(user_id) -> list[dict]:
    """Load OAuth accounts for a user (lazy='noload' requires explicit query)."""
    try:
        from core.config.app import alchemy
        from core.db.models.user.user_oauth_account import UserOAuthAccount
        from sqlalchemy import select

        async with alchemy.get_session() as session:
            stmt = select(UserOAuthAccount).where(UserOAuthAccount.user_id == user_id)
            result = await session.execute(stmt)
            return [
                {"provider": oa.oauth_name, "email": oa.account_email}
                for oa in result.scalars().all()
            ]
    except Exception:
        logger.warning(
            "Failed to load OAuth accounts for user %s", user_id, exc_info=True
        )
        return []
