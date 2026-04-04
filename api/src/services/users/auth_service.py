"""
Local authentication service — signup, login, JWT token creation.

Uses Litestar's built-in Token class for JWT encoding/decoding (HS256).
OIDC tokens from Microsoft/Oracle are still validated via python-jose (RS256).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from logging import getLogger
from typing import Any
from uuid import uuid4

from litestar.security.jwt import Token

from core.config.base import get_auth_settings
from core.db.models.user.user import User
from core.domain.users.service import UsersService
from core.exceptions import AuthError, ConflictError
from services.users.password import hash_password, verify_password
from services.users.refresh_token_service import create_refresh_token

logger = getLogger(__name__)


def create_access_token(
    user: User,
    auth_method: str = "password",
) -> str:
    """Create a signed JWT access token for a local user.

    Args:
        user: The authenticated User.
        auth_method: How the user authenticated ("password", "refresh", "oidc").

    Returns:
        Encoded JWT string.
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


async def signup(
    session: Any,
    email: str,
    password: str,
    name: str | None = None,
) -> User:
    """Register a new local user.

    Args:
        session: SQLAlchemy async session.
        email: User email (must be unique).
        password: Plaintext password (will be hashed).
        name: Optional display name.

    Returns:
        The created User.

    Raises:
        ConflictError: If email already exists.
    """
    service = UsersService(session=session)

    existing = await service.get_one_or_none(email=email)
    if existing is not None:
        raise ConflictError("Email already registered")

    hashed = hash_password(password)

    user = await service.create(
        User(
            email=email,
            name=name,
            hashed_password=hashed,
            is_active=True,
            is_verified=False,  # local users need to verify email
        ),
        auto_commit=False,
    )

    # Assign default role
    from services.users.service import _assign_default_role

    await _assign_default_role(session, user.id)

    return user


async def authenticate(
    session: Any,
    email: str,
    password: str,
) -> User:
    """Authenticate a user by email and password.

    Args:
        session: SQLAlchemy async session.
        email: User email.
        password: Plaintext password.

    Returns:
        The authenticated User.

    Raises:
        AuthError: If credentials are invalid or account inactive.
    """
    service = UsersService(session=session)

    user = await service.get_one_or_none(email=email)
    if user is None:
        raise AuthError("Invalid email or password")

    # Load deferred password field
    await session.refresh(user, attribute_names=["hashed_password"])

    if not user.hashed_password:
        raise AuthError("Invalid email or password")

    if not verify_password(password, user.hashed_password):
        raise AuthError("Invalid email or password")

    if not user.is_active:
        raise AuthError("Account is inactive")

    # Update last_login_at
    user.last_login_at = datetime.now(UTC)
    await service.update(user, auto_commit=False)

    return user


async def login(
    session: Any,
    email: str,
    password: str,
    device_info: str | None = None,
) -> tuple[str, str, User]:
    """Full login flow: authenticate + create access token + create refresh token.

    Returns:
        Tuple of (access_token, refresh_token_plaintext, user).
    """
    user = await authenticate(session, email, password)

    access_token = create_access_token(user, auth_method="password")

    refresh_plaintext, _ = await create_refresh_token(
        session=session,
        user_id=user.id,
        device_info=device_info,
    )

    return access_token, refresh_plaintext, user
