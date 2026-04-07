"""OAuth2 social login endpoints — Google, GitHub.

DEPRECATED: These endpoints are superseded by /api/v2/auth/sso/* (routes/auth_v2.py).
Kept for backward compatibility during migration. New code should use v2 SSO endpoints.

Flow:
1. GET /api/auth/oauth/{provider} → returns authorization URL + state
2. GET /api/auth/oauth/{provider}/callback → exchanges code for tokens, logs in user
"""

from __future__ import annotations

from logging import getLogger

from litestar import Controller, Response, get
from litestar.params import Parameter
from pydantic import BaseModel

from core.config.app import alchemy
from services.users import auth_service, oauth_service, refresh_token_service
from utils.cookies import set_auth_cookies

logger = getLogger(__name__)


class AuthorizationUrlResponse(BaseModel):
    authorization_url: str
    state: str


class OAuthController(Controller):
    path = "/auth/oauth"
    tags = ["Auth / OAuth"]

    @get(
        "/{provider:str}",
        exclude_from_auth=True,
        summary="Get OAuth authorization URL",
    )
    async def authorize(self, provider: str) -> AuthorizationUrlResponse:
        # ValidationError propagates to global exception handler → 422
        authorization_url, state = await oauth_service.get_authorization_url(provider)

        return AuthorizationUrlResponse(
            authorization_url=authorization_url,
            state=state,
        )

    @get(
        "/{provider:str}/callback",
        exclude_from_auth=True,
        summary="OAuth callback — exchange code for tokens",
    )
    async def callback(
        self,
        provider: str,
        code: str,
        oauth_state: str = Parameter(query="state"),
    ) -> Response:
        async with alchemy.get_session() as session:
            # AuthError propagates to global exception handler → 401
            user = await oauth_service.handle_oauth_callback(
                session=session,
                provider=provider,
                code=code,
                state=oauth_state,
            )

            # Create internal JWT tokens
            access_token = auth_service.create_access_token(user, auth_method="oauth")

            refresh_plaintext, _ = await refresh_token_service.create_refresh_token(
                session=session,
                user_id=user.id,
            )

            await session.commit()

        response = Response(
            {
                "access_token": access_token,
                "token_type": "bearer",
                "user_id": str(user.id),
            },
        )
        set_auth_cookies(response, access_token, refresh_plaintext)
        return response
