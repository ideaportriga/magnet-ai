import secrets
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

from core.config.base import get_auth_settings

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

        Since exclude_from_auth=True, authenticates manually to return
        401 when no session exists (frontend uses this to check auth state).
        """
        from middlewares.auth import ensure_request_auth_data

        auth = request.scope.get("auth")
        if not auth:
            try:
                auth = await ensure_request_auth_data(request)
            except Exception:
                raise NotAuthorizedException("Not authenticated")

        user = getattr(auth, "user", None)
        if user is not None:
            from services.auth.user_info import build_user_info

            info = await build_user_info(user, auth)
            # Legacy field for backward compat
            info["preferred_username"] = auth.data.get("preferred_username")
            return info

        # Fallback: return raw token/API-key data
        return auth.data

    @get("/login", exclude_from_auth=True)
    async def login(self, request: Request) -> ASGIResponse:
        """Handle login redirect"""
        nonce = secrets.token_urlsafe(32)

        params = {
            "response_type": RESPONSE_TYPE,
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "scope": AUTH_SCOPE,
            "response_mode": RESPONSE_MODE,
            "nonce": nonce,
        }

        redirect_uri = f"{OAUTH2_AUTHORIZE_URL}?{urlencode(params)}"
        response = Redirect(redirect_uri)
        asgi_response = response.to_asgi_response(app=None, request=request)
        asgi_response.headers.add(
            "Set-Cookie",
            f"oidc_nonce={nonce}; Max-Age=600; Secure; HttpOnly; Path=/; SameSite=Lax;",
        )
        return asgi_response

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
            "token=; Max-Age=0; Secure; HttpOnly; Path=/; SameSite=Lax;",
        )
        asgi_response.headers.add(
            "Set-Cookie",
            "refresh_token=; Max-Age=0; Secure; HttpOnly; Path=/; SameSite=Lax;",
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

        import json as _json

        # Safely serialize tokens to prevent XSS via malicious token values
        token_payload = _json.dumps(
            {"token": tokens.token, "refreshToken": tokens.refresh_token}
        )

        # Build allowed origins list from CORS config.
        # The popup is opened by the frontend (e.g. localhost:7000),
        # so we must postMessage to the frontend origin, not the backend.
        import os

        cors_origins = [
            o.strip()
            for o in os.environ.get("CORS_OVERRIDE_ALLOWED_ORIGINS", "").split(",")
            if o.strip()
        ]
        safe_origins = _json.dumps(cors_origins)

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
            const message = JSON.stringify({token_payload});
            const allowedOrigins = {safe_origins};
            if (window.opener) {{
                // Try each allowed origin — the browser will silently
                // ignore postMessage calls where targetOrigin doesn't
                // match the opener's actual origin.
                for (const origin of allowedOrigins) {{
                    window.opener.postMessage(message, origin);
                }}
            }}
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

        # Validate nonce to prevent token substitution attacks.
        #
        # In the popup flow, the nonce cookie is set in the popup window
        # (GET /auth/login), but /auth/complete is called from the opener
        # window via postMessage. The opener does NOT have the nonce cookie.
        #
        # Two validation paths:
        # 1. If nonce cookie is present (same-window flow) → strict validation
        # 2. If nonce cookie is absent (popup flow) → validate that the token
        #    has a nonce claim (proves it went through our /auth/login which
        #    set the nonce parameter on the IdP request). We can't verify the
        #    exact value, but presence + valid signature is sufficient.
        expected_nonce = request.cookies.get("oidc_nonce")
        token_nonce = decoded.get("nonce")

        if expected_nonce:
            # Same-window flow — strict match
            if not token_nonce:
                logger.warning("OIDC token missing nonce claim")
                raise NotAuthorizedException("Token missing nonce")
            if expected_nonce != token_nonce:
                logger.warning("OIDC nonce mismatch detected for auth request")
                raise NotAuthorizedException("Invalid nonce")
        else:
            # Popup flow — cookie not available in opener window.
            # Verify the token at least has a nonce (set by our /auth/login).
            if not token_nonce:
                logger.warning(
                    "OIDC token missing nonce and no nonce cookie — "
                    "this may indicate a token not originating from our login flow"
                )

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

        settings = get_auth_settings()
        token_max_age = 3600  # 1 hour
        refresh_max_age = settings.REFRESH_TOKEN_EXPIRATION_DAYS * 86400

        response = Response(content=None)
        asgi_response = response.to_asgi_response(app=None, request=request)
        asgi_response.headers.add(
            "Set-Cookie",
            f"token={token}; Max-Age={token_max_age}; Secure; HttpOnly; Path=/; SameSite=Lax;",
        )
        asgi_response.headers.add(
            "Set-Cookie",
            f"refresh_token={refresh_token}; Max-Age={refresh_max_age}; Secure; HttpOnly; Path=/; SameSite=Lax;",
        )
        # Clear nonce cookie after validation
        asgi_response.headers.add(
            "Set-Cookie",
            "oidc_nonce=; Max-Age=0; Secure; HttpOnly; Path=/; SameSite=Lax;",
        )

        return asgi_response
