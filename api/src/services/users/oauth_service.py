"""
OAuth2 social login service — Google, GitHub.

Uses httpx-oauth for provider-specific flows and Litestar JWT Token
for signing state tokens (CSRF protection).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from logging import getLogger
from typing import Any

from httpx_oauth.clients.github import GitHubOAuth2
from httpx_oauth.clients.google import GoogleOAuth2
from httpx_oauth.oauth2 import BaseOAuth2
from litestar.security.jwt import Token
from sqlalchemy import select

from core.config.base import get_auth_settings
from core.db.models.user.user import User
from core.db.models.user.user_oauth_account import UserOAuthAccount
from core.domain.users.service import UsersService
from services.users.service import _assign_default_role

logger = getLogger(__name__)

# State token lifetime for CSRF protection
STATE_TOKEN_LIFETIME = timedelta(minutes=10)


def get_oauth_client(provider: str) -> BaseOAuth2:
    """Get the httpx-oauth client for a given provider.

    Raises:
        ValueError: If provider is not configured or unknown.
    """
    settings = get_auth_settings()

    if provider == "google":
        if not settings.GOOGLE_OAUTH2_CLIENT_ID:
            raise ValueError("Google OAuth2 is not configured")
        return GoogleOAuth2(
            client_id=settings.GOOGLE_OAUTH2_CLIENT_ID,
            client_secret=settings.GOOGLE_OAUTH2_CLIENT_SECRET,
        )
    elif provider == "github":
        if not settings.GITHUB_OAUTH2_CLIENT_ID:
            raise ValueError("GitHub OAuth2 is not configured")
        return GitHubOAuth2(
            client_id=settings.GITHUB_OAUTH2_CLIENT_ID,
            client_secret=settings.GITHUB_OAUTH2_CLIENT_SECRET,
        )
    else:
        raise ValueError(f"Unknown OAuth provider: {provider}")


def get_redirect_url(provider: str) -> str:
    """Build the callback URL for a provider."""
    settings = get_auth_settings()
    return f"{settings.OAUTH2_REDIRECT_BASE_URL}/api/auth/oauth/{provider}/callback"


def create_state_token(provider: str) -> str:
    """Create a signed JWT state token for CSRF protection."""
    settings = get_auth_settings()
    token = Token(
        sub=provider,
        exp=datetime.now(UTC) + STATE_TOKEN_LIFETIME,
        extras={"provider": provider},
    )
    return token.encode(
        secret=settings.SECRET_KEY,
        algorithm=settings.JWT_ENCRYPTION_ALGORITHM,
    )


def validate_state_token(state: str, expected_provider: str) -> bool:
    """Validate the state token and check provider matches."""
    settings = get_auth_settings()
    try:
        token = Token.decode(
            encoded_token=state,
            secret=settings.SECRET_KEY,
            algorithm=settings.JWT_ENCRYPTION_ALGORITHM,
        )
        return (token.extras or {}).get("provider") == expected_provider
    except Exception:
        return False


async def get_authorization_url(provider: str) -> tuple[str, str]:
    """Get the authorization URL and state token for a provider.

    Returns:
        Tuple of (authorization_url, state_token).
    """
    client = get_oauth_client(provider)
    redirect_url = get_redirect_url(provider)
    state = create_state_token(provider)

    scopes = _get_scopes(provider)

    authorization_url = await client.get_authorization_url(
        redirect_uri=redirect_url,
        state=state,
        scope=scopes,
    )

    return authorization_url, state


async def handle_oauth_callback(
    session: Any,
    provider: str,
    code: str,
    state: str,
) -> User:
    """Exchange auth code for tokens, find/create user, link OAuth account.

    Args:
        session: SQLAlchemy async session.
        provider: OAuth provider name.
        code: Authorization code from callback.
        state: State token for CSRF validation.

    Returns:
        The authenticated User.

    Raises:
        ValueError: If state is invalid or user info cannot be retrieved.
    """
    if not validate_state_token(state, provider):
        raise ValueError("Invalid or expired OAuth state token")

    client = get_oauth_client(provider)
    redirect_url = get_redirect_url(provider)

    # Exchange code for tokens
    oauth2_token = await client.get_access_token(code=code, redirect_uri=redirect_url)

    access_token = oauth2_token["access_token"]
    refresh_token = oauth2_token.get("refresh_token")
    expires_at = oauth2_token.get("expires_at")

    # Get user info from provider
    account_id, account_email, account_name = await _get_user_info(
        client, provider, access_token
    )

    if not account_email:
        raise ValueError("OAuth provider did not return an email address")

    now = datetime.now(UTC)

    # Find or create internal User
    service = UsersService(session=session)
    user = await service.get_one_or_none(email=account_email)

    if user is None:
        user = await service.create(
            User(
                email=account_email,
                name=account_name,
                is_active=True,
                is_verified=True,  # OAuth-verified emails
                last_login_at=now,
            ),
            auto_commit=False,
        )
        await _assign_default_role(session, user.id)
        logger.info("Created new user from OAuth %s: %s", provider, account_email)
    else:
        user.last_login_at = now
        if account_name and user.name != account_name:
            user.name = account_name

    # Upsert OAuth account link
    stmt = select(UserOAuthAccount).where(
        UserOAuthAccount.oauth_name == provider,
        UserOAuthAccount.account_id == account_id,
    )
    result = await session.execute(stmt)
    oauth_account = result.scalar_one_or_none()

    if oauth_account is None:
        oauth_account = UserOAuthAccount(
            user_id=user.id,
            oauth_name=provider,
            account_id=account_id,
            account_email=account_email,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            last_login_at=now,
        )
        session.add(oauth_account)
    else:
        oauth_account.access_token = access_token
        oauth_account.refresh_token = refresh_token
        oauth_account.expires_at = expires_at
        oauth_account.last_login_at = now
        if account_email != oauth_account.account_email:
            oauth_account.account_email = account_email

    return user


async def _get_user_info(
    client: BaseOAuth2,
    provider: str,
    access_token: str,
) -> tuple[str, str | None, str | None]:
    """Fetch user info from OAuth provider.

    Returns:
        Tuple of (account_id, email, name).
    """
    import httpx

    if provider == "google":
        async with httpx.AsyncClient() as http_client:
            resp = await http_client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            resp.raise_for_status()
            data = resp.json()
            return str(data["id"]), data.get("email"), data.get("name")

    elif provider == "github":
        async with httpx.AsyncClient() as http_client:
            resp = await http_client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            resp.raise_for_status()
            data = resp.json()
            email = data.get("email")
            # GitHub may not return email in profile; fetch from emails API
            if not email:
                emails_resp = await http_client.get(
                    "https://api.github.com/user/emails",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                emails_resp.raise_for_status()
                for e in emails_resp.json():
                    if e.get("primary") and e.get("verified"):
                        email = e["email"]
                        break
            return str(data["id"]), email, data.get("name") or data.get("login")

    raise ValueError(f"Unsupported provider for user info: {provider}")


def _get_scopes(provider: str) -> list[str]:
    """Get OAuth scopes for a provider."""
    if provider == "google":
        return ["openid", "email", "profile"]
    elif provider == "github":
        return ["user:email", "read:user"]
    return []
