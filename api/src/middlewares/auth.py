"""Authentication middleware.

Supports authentication methods (checked in order):
1. API Key (`x-api-key` header) for M2M access
2. Internal JWT (cookie or Authorization header), signed with `SECRET_KEY`

Legacy OIDC token validation is intentionally removed. All user auth flows
must go through unified v2 auth endpoints that issue internal JWTs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from logging import getLogger
from typing import TYPE_CHECKING, Final, Literal

from litestar.connection import ASGIConnection
from litestar.enums import ScopeType
from litestar.exceptions import NotAuthorizedException
from litestar.middleware import AbstractMiddleware
from litestar.security.jwt import Token
from litestar.types import Receive, Scope, Send

from core.config.base import get_auth_settings
from services.api_keys.deprecated import get_api_key_client_mapping
from services.api_keys.services import get_api_key_config

if TYPE_CHECKING:
    from core.db.models.user.user import User

logger = getLogger(__name__)

API_KEY_HEADER_NAME: Final[str] = "x-api-key"
API_USER_ID_HEADER_NAME: Final[str] = "x-user-id"
API_KEY_CLIENT_MAPPING_DEPRECATED: Final = get_api_key_client_mapping()


@dataclass
class Auth:
    data: dict
    user_id: str | None
    type: Literal["api_key", "local_jwt"]
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

            await self.app(scope, receive, send)

    return AuthResponseMiddleware


async def ensure_request_auth_data_local_jwt(token_str: str) -> Auth | None:
    """Try to decode a local JWT signed with SECRET_KEY.

    Returns `Auth` on success, otherwise `None`.
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
        return None

    extras = token.extras or {}
    user_id = extras.get("user_id")

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

    scopes = None
    try:
        api_key_config = get_api_key_config(api_key)
        scopes = getattr(api_key_config, "scopes", None)
    except (KeyError, AttributeError):
        pass

    return Auth(
        type="api_key",
        data={
            "api_client_code": api_client_code,
            "user_id": user_id,
            "roles": {"user"},
            "preferred_username": api_client_code,
            "scopes": scopes,
        },
        user_id=user_id,
    )


async def ensure_request_auth_data(connection: ASGIConnection) -> Auth:
    # 1. API Key (highest priority — M2M access)
    api_key = connection.headers.get(API_KEY_HEADER_NAME)
    api_user_id = connection.headers.get(API_USER_ID_HEADER_NAME)

    if api_key:
        return ensure_request_auth_data_api_key(
            api_key=api_key,
            api_user_id=api_user_id,
        )

    # 2. Token from cookie (internal JWT)
    token = connection.cookies.get("token")
    if token:
        local_auth = await ensure_request_auth_data_local_jwt(token)
        if local_auth is not None:
            return local_auth

    # 3. Authorization header (Bearer token — internal JWT)
    auth_header = connection.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        bearer_token = auth_header[7:]
        local_auth = await ensure_request_auth_data_local_jwt(bearer_token)
        if local_auth is not None:
            return local_auth

    logger.warning("No valid auth data provided")
    raise NotAuthorizedException()
