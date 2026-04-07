"""
Unified session service — creates internal sessions for any auth flow.

All authentication flows (local, OIDC, OAuth social, broker) end here.
The output is always the same: an internal HS256 JWT + a family-based refresh token.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from logging import getLogger
from typing import TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from litestar.security.jwt import Token

from core.config.base import get_auth_settings
from core.db.models.user.user import User
from services.users.refresh_token_service import create_refresh_token

logger = getLogger(__name__)


@dataclass
class InternalSession:
    """Result of any successful authentication."""

    access_token: str
    refresh_token: str  # plaintext — goes into cookie, hash stored in DB
    user: User


def create_access_token(
    user: User,
    auth_method: str = "password",
) -> str:
    """Create a signed HS256 JWT access token.

    This is the single canonical access token format for Magnet AI.
    External tokens (OIDC RS256) are never stored in cookies — they are only
    used during the callback for identity resolution.
    """
    settings = get_auth_settings()
    role_slugs = [r.slug for r in (user.roles or [])]

    token = Token(
        sub=user.email,
        exp=datetime.now(UTC)
        + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRATION_MINUTES),
        jti=str(uuid4()),
        extras={
            "user_id": str(user.id),
            "is_superuser": user.is_superuser,
            "is_verified": user.is_verified,
            "auth_method": auth_method,
            "roles": role_slugs,
        },
    )
    return token.encode(
        secret=settings.SECRET_KEY,
        algorithm=settings.JWT_ENCRYPTION_ALGORITHM,
    )


async def create_session(
    session: "AsyncSession",
    user: User,
    device_info: str | None = None,
    auth_method: str = "password",
) -> InternalSession:
    """Create an internal session for any auth flow.

    This is the single entry point for session creation.
    All auth strategies should call this after resolving identity.
    """
    access_token = create_access_token(user, auth_method=auth_method)

    refresh_plaintext, _ = await create_refresh_token(
        session=session,
        user_id=user.id,
        device_info=device_info,
    )

    return InternalSession(
        access_token=access_token,
        refresh_token=refresh_plaintext,
        user=user,
    )
