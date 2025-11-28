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

    @get("/me")
    async def get_current_user(self, request: Request) -> dict:
        """Get current user information"""
        return request.auth.data

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
        """Complete authentication"""
        token = data.get("token", "")
        refresh_token = data.get("refreshToken", "")

        try:
            await decode_token(token)
        except Exception:
            raise NotAuthorizedException()

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
