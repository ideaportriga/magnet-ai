"""
Local authentication service — signup, login, credential verification.

For token creation, use services.auth.session_service.create_access_token()
and services.auth.session_service.create_session().
"""

from __future__ import annotations

from datetime import UTC, datetime
from logging import getLogger
from typing import Any

from core.db.models.user.user import User
from core.domain.users.service import UsersService
from core.exceptions import AuthError, ConflictError
from services.users.password import hash_password_async, verify_password_async
from services.users.refresh_token_service import create_refresh_token

logger = getLogger(__name__)


# Re-export for backward compatibility — canonical version is in session_service
def create_access_token(
    user: User,
    auth_method: str = "password",
) -> str:
    """Create a signed JWT access token. Delegates to session_service."""
    from services.auth.session_service import create_access_token as _create

    return _create(user, auth_method=auth_method)


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

    hashed = await hash_password_async(password)

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

    if not await verify_password_async(password, user.hashed_password):
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
