from logging import getLogger
from typing import Annotated
from urllib.parse import urlencode

from litestar import Controller, MediaType, Request, get, post
from litestar.enums import RequestEncodingType
from litestar.exceptions import ClientException, NotAuthorizedException
from litestar.params import Body
from litestar.response import Redirect, Response
from litestar.response.base import ASGIResponse
from litestar.status_codes import HTTP_200_OK

from config.auth import (
    AUTH_SCOPE,
    CLIENT_ID,
    OAUTH2_AUTHORIZE_URL,
    REDIRECT_URI,
    RESPONSE_MODE,
    RESPONSE_TYPE,
    decode_token,
    redeem_code,
)

logger = getLogger(__name__)


class AuthController(Controller):
    path = "/auth"
    tags = ["auth"]

    @get("/me", exclude_from_auth=True)
    async def get_current_user(self, request: Request) -> dict:
        """Get current user information.

        Returns enriched data from the User DB record when available,
        with fallback to OIDC/API-key token data.
        Returns 401 if no valid session exists (used by frontend to check auth state).
        """
        # Since exclude_from_auth=True, middleware may not have set scope["auth"].
        # Try to authenticate manually.
        from middlewares.auth import ensure_request_auth_data

        auth = request.scope.get("auth")
        if not auth:
            try:
                auth = await ensure_request_auth_data(request)
            except Exception:
                raise NotAuthorizedException("Not authenticated")
        user = getattr(auth, "user", None)

        if user is not None:
            # Build response from user object (roles are selectin-loaded)
            roles = []
            try:
                roles = [r.slug for r in (user.roles or [])]
            except Exception:
                pass

            # oauth_accounts are lazy="noload" — load them explicitly
            oauth_accounts = []
            try:
                from core.config.app import alchemy
                from core.db.models.user.user_oauth_account import UserOAuthAccount
                from sqlalchemy import select

                async with alchemy.get_session() as session:
                    stmt = select(UserOAuthAccount).where(
                        UserOAuthAccount.user_id == user.id
                    )
                    result = await session.execute(stmt)
                    for oa in result.scalars().all():
                        oauth_accounts.append(
                            {
                                "provider": oa.oauth_name,
                                "email": oa.account_email,
                            }
                        )
            except Exception:
                pass

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
                "last_login_at": user.last_login_at.isoformat()
                if user.last_login_at
                else None,
                "preferred_username": auth.data.get("preferred_username"),
                "oauth_accounts": oauth_accounts,
            }

        # Fallback: return raw token/API-key data
        return auth.data

    @get("/login", exclude_from_auth=True)
    async def login(self) -> Redirect:
        """Handle login redirect"""
        login_hint = ""

        params = {
            "response_type": RESPONSE_TYPE,
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "scope": AUTH_SCOPE,
            "response_mode": RESPONSE_MODE,
            "nonce": "12345",  # TODO - receive as param
            "login_hint": login_hint,
        }

        redirect_uri = f"{OAUTH2_AUTHORIZE_URL}?{urlencode(params)}"
        return Redirect(redirect_uri)

    @post("/logout", status_code=HTTP_200_OK, exclude_from_auth=True)
    async def logout(
        self,
        request: Request,
    ) -> ASGIResponse:
        """Delete auth cookies"""
        response = Response(content=None)
        asgi_response = response.to_asgi_response(app=None, request=request)
        asgi_response.headers.add(
            "Set-Cookie",
            "token=; Max-Age=0; Secure; HttpOnly; Path=/; SameSite=None; Partitioned;",
        )
        asgi_response.headers.add(
            "Set-Cookie",
            "refresh_token=; Max-Age=0; Secure; HttpOnly; Path=/; SameSite=None; Partitioned;",
        )

        return asgi_response

    @post(
        "/callback",
        status_code=HTTP_200_OK,
        exclude_from_auth=True,
        media_type=MediaType.HTML,
    )
    async def auth_callback_form(
        self,
        data: Annotated[dict, Body(media_type=RequestEncodingType.URL_ENCODED)],
    ) -> str:
        """Handle auth callback"""
        code = data.get("code")
        if not code:
            raise ClientException("Code is missing")

        tokens = await redeem_code(code)

        auth_completion_page = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Popup Callback Page</title>
        </head>
        <script>
        completeLogin()

        function completeLogin() {{
            // TODO - change "*" to specific origin
            // TODO - set additional info (identifier, nonce?)
            const message = JSON.stringify({{
            token: "{tokens.token}",
            refreshToken: "{tokens.refresh_token}",
            }})
            window.opener.postMessage(message, '*');
            window.close();
        }}

        </script>
        <body>
        </body>
        </html>
        """

        return auth_completion_page

    @post("/complete", status_code=HTTP_200_OK, exclude_from_auth=True)
    async def auth_complete(
        self,
        request: Request,
        data: dict = Body(),
    ) -> ASGIResponse:
        """Complete authentication — sets cookies and creates internal session."""
        token = data.get("token", "")
        refresh_token = data.get("refreshToken", "")

        try:
            decoded = await decode_token(token)
        except Exception:
            raise NotAuthorizedException()

        # Create internal session for OIDC users (for session tracking)
        try:
            from config.auth import USER_ID_KEY, AUTH_PROVIDER
            from middlewares.auth import get_auth_data_from_decoded_token
            from services.users.service import upsert_user_from_oidc
            from services.users.refresh_token_service import create_refresh_token
            from core.config.app import alchemy

            auth_data = get_auth_data_from_decoded_token(decoded)
            oauth_name = AUTH_PROVIDER.lower()
            account_id = str(decoded.get(USER_ID_KEY, ""))

            if account_id:
                user = await upsert_user_from_oidc(
                    auth_data=auth_data,
                    oauth_name=oauth_name,
                    account_id=account_id,
                )
                if user:
                    device_info = request.headers.get("user-agent")
                    async with alchemy.get_session() as session:
                        await create_refresh_token(
                            session=session,
                            user_id=user.id,
                            device_info=device_info,
                        )
                        await session.commit()
        except Exception:
            # Best-effort — don't block auth completion
            import logging

            logging.getLogger(__name__).exception(
                "Failed to create session for OIDC user"
            )

        response = Response(content=None)
        asgi_response = response.to_asgi_response(app=None, request=request)
        asgi_response.headers.add(
            "Set-Cookie",
            f"token={token}; Secure; HttpOnly; Path=/; SameSite=None; Partitioned;",
        )
        asgi_response.headers.add(
            "Set-Cookie",
            f"refresh_token={refresh_token}; Secure; HttpOnly; Path=/; SameSite=None; Partitioned;",
        )

        return asgi_response
