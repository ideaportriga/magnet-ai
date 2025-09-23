from dataclasses import dataclass
from logging import getLogger
from typing import Any, Final, Literal

from jose import ExpiredSignatureError
from litestar.connection import ASGIConnection
from litestar.datastructures import MutableScopeHeaders
from litestar.enums import ScopeType
from litestar.exceptions import NotAuthorizedException
from litestar.middleware import AbstractMiddleware
from litestar.types import Message, Receive, Scope, Send

from config.auth import (
    API_KEY_HEADER_NAME,
    API_USER_ID_HEADER_NAME,
    USER_ID_KEY,
    Tokens,
    decode_token,
    get_tokens,
)

from services.api_keys.deprecated import get_api_key_client_mapping
from services.api_keys.services import get_api_key_config

logger = getLogger(__name__)

API_KEY_CLIENT_MAPPING_DEPRECATED: Final = get_api_key_client_mapping()

@dataclass
class Auth:
    data: dict
    user_id: str | None
    type: Literal["token", "api_key"]
    tokens_refreshed: Tokens | None = None


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
                        headers = MutableScopeHeaders.from_message(message=message)
                        headers.add(
                            "Set-Cookie",
                            f"token={auth.tokens_refreshed.token}; Secure; HttpOnly; Path=/; SameSite=None; Partitioned;",
                        )
                        headers.add(
                            "Set-Cookie",
                            f"refresh_token={auth.tokens_refreshed.refresh_token}; Secure; HttpOnly; Path=/; SameSite=None; Partitioned;",
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


async def ensure_request_auth_data_oidc(
    token: str,
    refresh_token: str | None,
) -> Auth:
    tokens_refreshed = None

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
        token_refreshed_decoded = await decode_token(token_refreshed)

        auth_data = get_auth_data_from_decoded_token(token_refreshed_decoded)

    return Auth(
        type="token",
        data=auth_data,
        tokens_refreshed=tokens_refreshed,
        user_id=auth_data.get("user_id"),
    )


def ensure_request_auth_data_api_key(api_key: str, api_user_id: str | None) -> Auth:
    api_client_code = None

    try:
        api_key_config = get_api_key_config(api_key)
        api_client_code = api_key_config.name
    except KeyError:
        logger.warning("API key not found")
        # raise NotAuthorizedException("API key not found")
    
        
        # Deprecated: TODO - remove after transition to new API keys and raise NotAuthorizedException instead
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
            # All API keys has admin access
            # This could be changed with introduction of different API key roles
            "roles": {"admin"},
        },
        user_id=user_id,  # TODO - add user_id
    )


async def ensure_request_auth_data(connection: ASGIConnection) -> Auth:
    api_key = connection.headers.get(API_KEY_HEADER_NAME)
    api_user_id = connection.headers.get(API_USER_ID_HEADER_NAME)

    if api_key:
        return ensure_request_auth_data_api_key(
            api_key=api_key,
            api_user_id=api_user_id,
        )

    token = connection.cookies.get("token")
    refresh_token = connection.cookies.get("refresh_token")

    if token:
        return await ensure_request_auth_data_oidc(
            token=token,
            refresh_token=refresh_token,
        )

    logger.warning("No auth data provided")

    raise NotAuthorizedException()
