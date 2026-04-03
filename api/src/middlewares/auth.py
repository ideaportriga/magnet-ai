"""Authentication middleware.

Supports three authentication methods (checked in order):
1. API Key (x-api-key header)
2. Local JWT (cookie or Authorization header) — signed with SECRET_KEY (HS256)
3. OIDC token (cookie) — signed by external IdP with RS256

Local JWT tokens are created by our /api/auth/login endpoint.
OIDC tokens come from Microsoft Entra ID or Oracle OIDC.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from logging import getLogger
from typing import TYPE_CHECKING, Any, Final, Literal

from jose import ExpiredSignatureError
from litestar.connection import ASGIConnection
from litestar.datastructures import MutableScopeHeaders
from litestar.enums import ScopeType
from litestar.exceptions import NotAuthorizedException
from litestar.middleware import AbstractMiddleware
from litestar.security.jwt import Token
from litestar.types import Message, Receive, Scope, Send

from config.auth import (
    API_KEY_HEADER_NAME,
    API_USER_ID_HEADER_NAME,
    AUTH_PROVIDER,
    USER_ID_KEY,
    Tokens,
    decode_token,
    get_tokens,
)
from core.config.base import get_auth_settings
from services.api_keys.deprecated import get_api_key_client_mapping
from services.api_keys.services import get_api_key_config

if TYPE_CHECKING:
    from core.db.models.user.user import User

logger = getLogger(__name__)

API_KEY_CLIENT_MAPPING_DEPRECATED: Final = get_api_key_client_mapping()


@dataclass
class Auth:
    data: dict
    user_id: str | None
    type: Literal["token", "api_key", "local_jwt"]
    tokens_refreshed: Tokens | None = None
    user: User | None = field(default=None, repr=False)


def create_auth_middleware(
    exclude_param: str | list[str] | None = None,
) -> type[AbstractMiddleware]:
    class AuthResponseMiddleware(AbstractMiddleware):
        scopes = {ScopeType.HTTP}
        exclude_opt_key = "exclude_from_auth"
        exclude = exclude_param or None

        async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
            auth = await ensure_request_auth_data(ASGIConnection(scope))

            scope["auth"] = auth
            scope["user_id"] = auth.user_id  # type: ignore

            async def send_wrapper(message: Message) -> None:
                if message["type"] == "http.response.start":
                    if auth.tokens_refreshed:
                        settings = get_auth_settings()
                        token_max_age = 3600  # 1 hour
                        refresh_max_age = settings.REFRESH_TOKEN_EXPIRATION_DAYS * 86400
                        headers = MutableScopeHeaders.from_message(message=message)
                        headers.add(
                            "Set-Cookie",
                            f"token={auth.tokens_refreshed.token}; Max-Age={token_max_age}; Secure; HttpOnly; Path=/; SameSite=None; Partitioned;",
                        )
                        headers.add(
                            "Set-Cookie",
                            f"refresh_token={auth.tokens_refreshed.refresh_token}; Max-Age={refresh_max_age}; Secure; HttpOnly; Path=/; SameSite=None; Partitioned;",
                        )

                await send(message)

            await self.app(scope, receive, send_wrapper)

    return AuthResponseMiddleware


async def refresh_tokens(refresh_token: str) -> Tokens:
    aditional_data = {"grant_type": "refresh_token", "refresh_token": refresh_token}
    return await get_tokens(aditional_data)


def get_auth_data_from_decoded_token(decoded_token: dict[str, Any]) -> dict:
    auth_data = {
        "user_id": decoded_token.get(USER_ID_KEY),
        "name": decoded_token.get("name"),
        "email": decoded_token.get("email"),
        "preferred_username": decoded_token.get("preferred_username"),
        "roles": set(decoded_token.get("roles", [])),
        "exp": decoded_token.get("exp"),
    }
    return auth_data


# --- Local JWT ---


async def ensure_request_auth_data_local_jwt(token_str: str) -> Auth | None:
    """Try to decode a local JWT (HS256, signed with SECRET_KEY).

    Returns Auth on success, None if not a local JWT (wrong signature, etc.).
    """
    settings = get_auth_settings()
    if not settings.SECRET_KEY:
        return None

    try:
        token = Token.decode(
            encoded_token=token_str,
            secret=settings.SECRET_KEY,
            algorithm=settings.JWT_ENCRYPTION_ALGORITHM,
        )
    except Exception:
        # Not a local JWT — fall through to OIDC
        return None

    extras = token.extras or {}
    user_id = extras.get("user_id")

    # Load User from DB
    user = None
    if user_id:
        try:
            from services.users.service import get_user_by_id

            user = await get_user_by_id(user_id)
        except Exception:
            logger.exception("Failed to load user for local JWT")

    auth_data = {
        "user_id": user_id,
        "email": token.sub,
        "name": user.name if user else None,
        "preferred_username": token.sub,
        "roles": set(extras.get("roles", [])),
        "exp": token.exp.timestamp() if token.exp else None,
        "is_superuser": extras.get("is_superuser", False),
        "is_verified": extras.get("is_verified", False),
        "auth_method": extras.get("auth_method", "password"),
    }

    return Auth(
        type="local_jwt",
        data=auth_data,
        user_id=user_id,
        user=user,
    )


# --- OIDC ---


async def ensure_request_auth_data_oidc(
    token: str,
    refresh_token: str | None,
) -> Auth:
    tokens_refreshed = None
    decoded_token = None

    try:
        decoded_token = await decode_token(token)
        auth_data = get_auth_data_from_decoded_token(decoded_token)

    except ExpiredSignatureError as exc:
        if not refresh_token:
            raise NotAuthorizedException(
                "Token expired and refresh_token does not exist",
            ) from exc

        tokens_refreshed = await refresh_tokens(refresh_token)
        token_refreshed = tokens_refreshed.token
        decoded_token = await decode_token(token_refreshed)

        auth_data = get_auth_data_from_decoded_token(decoded_token)

    # Upsert internal User record (best-effort)
    user = await _try_upsert_oidc_user(auth_data, decoded_token)

    return Auth(
        type="token",
        data=auth_data,
        tokens_refreshed=tokens_refreshed,
        user_id=auth_data.get("user_id"),
        user=user,
    )


# --- API Key ---


def ensure_request_auth_data_api_key(api_key: str, api_user_id: str | None) -> Auth:
    api_client_code = None

    try:
        api_key_config = get_api_key_config(api_key)
        api_client_code = api_key_config.name
    except KeyError:
        logger.warning("API key not found")

        # Deprecated: TODO - remove after transition to new API keys
        if api_key not in API_KEY_CLIENT_MAPPING_DEPRECATED:
            raise NotAuthorizedException("Deprecated API key not found")

        api_client_code = API_KEY_CLIENT_MAPPING_DEPRECATED[api_key]

    user_id = f"api_key:{api_client_code}"
    if api_user_id:
        user_id += f":{api_user_id}"

    return Auth(
        type="api_key",
        data={
            "api_client_code": api_client_code,
            "user_id": user_id,
            # All API keys have admin access
            "roles": {"admin"},
            "preferred_username": api_client_code,
        },
        user_id=user_id,
    )


# --- Main dispatcher ---


async def ensure_request_auth_data(connection: ASGIConnection) -> Auth:
    # 1. API Key (highest priority — M2M access)
    api_key = connection.headers.get(API_KEY_HEADER_NAME)
    api_user_id = connection.headers.get(API_USER_ID_HEADER_NAME)

    if api_key:
        return ensure_request_auth_data_api_key(
            api_key=api_key,
            api_user_id=api_user_id,
        )

    # 2. Token from cookie (could be local JWT or OIDC)
    token = connection.cookies.get("token")
    refresh_token = connection.cookies.get("refresh_token")

    if token:
        # Try local JWT first (fast, no network calls)
        local_auth = await ensure_request_auth_data_local_jwt(token)
        if local_auth is not None:
            return local_auth

        # Fall back to OIDC token validation
        return await ensure_request_auth_data_oidc(
            token=token,
            refresh_token=refresh_token,
        )

    # 3. Authorization header (Bearer token — local JWT only)
    auth_header = connection.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        bearer_token = auth_header[7:]
        local_auth = await ensure_request_auth_data_local_jwt(bearer_token)
        if local_auth is not None:
            return local_auth

    logger.warning("No auth data provided")
    raise NotAuthorizedException()


async def _try_upsert_oidc_user(auth_data: dict, decoded_token: dict) -> User | None:
    """Best-effort upsert of internal User from OIDC token."""
    try:
        from services.users.service import upsert_user_from_oidc

        oauth_name = AUTH_PROVIDER.lower()
        account_id = str(decoded_token.get(USER_ID_KEY, ""))

        if not account_id:
            logger.warning(
                "OIDC token missing %s claim — skipping user upsert", USER_ID_KEY
            )
            return None

        return await upsert_user_from_oidc(
            auth_data=auth_data,
            oauth_name=oauth_name,
            account_id=account_id,
        )
    except Exception:
        logger.exception("Failed to upsert user from OIDC token")
        return None
