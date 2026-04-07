"""MFA (Multi-Factor Authentication) endpoints.

DEPRECATED: These endpoints are superseded by /api/v2/auth/mfa/* (routes/auth_v2.py).
Kept for backward compatibility during migration. New code should use v2 MFA endpoints.

Flow:
1. GET  /api/auth/mfa/setup         → QR code + secret
2. POST /api/auth/mfa/setup/confirm → verify TOTP code, save, return backup codes
3. POST /api/auth/mfa/verify        → verify during login (TOTP or backup code)
4. DELETE /api/auth/mfa             → disable MFA (requires password)
"""

from __future__ import annotations

from logging import getLogger
from typing import Optional

from litestar import Controller, Response, delete, get, post
from litestar.connection import Request
from litestar.exceptions import NotAuthorizedException
from pydantic import BaseModel, Field

from core.config.app import alchemy
from middlewares.auth import Auth
from services.users import auth_service, mfa_service, refresh_token_service
from utils.cookies import set_auth_cookies

logger = getLogger(__name__)


# --- Schemas ---


class MfaSetupResponse(BaseModel):
    secret: str
    provisioning_uri: str
    qr_code: str  # base64 PNG


class MfaConfirmRequest(BaseModel):
    secret: str = Field(..., description="TOTP secret from setup step")
    totp_code: str = Field(
        ..., min_length=6, max_length=6, description="6-digit TOTP code"
    )


class MfaConfirmResponse(BaseModel):
    backup_codes: list[str]
    message: str = "MFA enabled successfully. Save your backup codes — they cannot be retrieved later."


class MfaVerifyRequest(BaseModel):
    code: str = Field(..., description="6-digit TOTP code or 8-char backup code")


class MfaDisableRequest(BaseModel):
    password: Optional[str] = Field(
        None, description="Current password (required for password users)"
    )


# --- Controller ---


class MfaController(Controller):
    path = "/auth/mfa"
    tags = ["Auth / MFA"]

    @staticmethod
    async def before_request(request: "Request") -> None:  # type: ignore[override]
        from middlewares.rate_limit import check_rate_limit

        check_rate_limit(request)

    @get("/setup", summary="Begin MFA setup — get QR code and secret")
    async def setup(self, request: Request) -> MfaSetupResponse:
        auth: Auth = request.scope.get("auth")
        if not auth or not auth.user:
            raise NotAuthorizedException("Authentication required")

        if auth.user.is_two_factor_enabled:
            raise NotAuthorizedException("MFA is already enabled")

        result = await mfa_service.setup_mfa(auth.user)
        return MfaSetupResponse(**result)

    @post("/setup/confirm", summary="Confirm MFA setup with TOTP code")
    async def confirm_setup(
        self, request: Request, data: MfaConfirmRequest
    ) -> MfaConfirmResponse:
        auth: Auth = request.scope.get("auth")
        if not auth or not auth.user:
            raise NotAuthorizedException("Authentication required")

        async with alchemy.get_session() as session:
            # Re-fetch user within this session
            from core.domain.users.service import UsersService

            service = UsersService(session=session)
            user = await service.get(auth.user.id)

            # AuthError propagates to global exception handler → 401
            backup_codes = await mfa_service.confirm_mfa_setup(
                session=session,
                user=user,
                secret=data.secret,
                totp_code=data.totp_code,
            )

            await session.commit()

        return MfaConfirmResponse(backup_codes=backup_codes)

    @post(
        "/verify",
        exclude_from_auth=True,
        summary="Verify MFA code during login",
    )
    async def verify(self, request: Request, data: MfaVerifyRequest) -> Response:
        # The mfa_challenge cookie contains a JWT with user_id
        mfa_cookie = request.cookies.get("mfa_challenge")
        if not mfa_cookie:
            raise NotAuthorizedException("MFA challenge not found — please login first")

        from litestar.security.jwt import Token

        from core.config.base import get_auth_settings

        settings = get_auth_settings()

        try:
            token = Token.decode(
                encoded_token=mfa_cookie,
                secret=settings.SECRET_KEY,
                algorithm=settings.JWT_ENCRYPTION_ALGORITHM,
            )
        except Exception as e:
            raise NotAuthorizedException("Invalid or expired MFA challenge") from e

        user_id = (token.extras or {}).get("user_id")
        if not user_id:
            raise NotAuthorizedException("Invalid MFA challenge token")

        async with alchemy.get_session() as session:
            from core.domain.users.service import UsersService

            service = UsersService(session=session)
            user = await service.get_one_or_none(id=user_id)
            if not user:
                raise NotAuthorizedException("User not found")

            verified = await mfa_service.verify_mfa(
                session=session, user=user, code=data.code
            )
            if not verified:
                raise NotAuthorizedException("Invalid MFA code")

            # MFA passed — issue real tokens
            access_token = auth_service.create_access_token(
                user, auth_method="password"
            )
            device_info = request.headers.get("user-agent")
            refresh_plaintext, _ = await refresh_token_service.create_refresh_token(
                session=session,
                user_id=user.id,
                device_info=device_info,
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
        # Clear the MFA challenge cookie
        response.delete_cookie(key="mfa_challenge", path="/api/auth/mfa")
        return response

    @delete("/", summary="Disable MFA (requires password)", status_code=200)
    async def disable(self, request: Request, data: MfaDisableRequest) -> dict:
        auth: Auth = request.scope.get("auth")
        if not auth or not auth.user:
            raise NotAuthorizedException("Authentication required")

        if not auth.user.is_two_factor_enabled:
            return {"message": "MFA is not enabled"}

        async with alchemy.get_session() as session:
            from core.domain.users.service import UsersService

            service = UsersService(session=session)
            user = await service.get(auth.user.id)
            await session.refresh(user, attribute_names=["hashed_password"])

            if user.hashed_password:
                # Password-based users must confirm their password
                if not data.password:
                    raise NotAuthorizedException("Password required to disable MFA")

                from services.users.password import verify_password_async

                if not await verify_password_async(data.password, user.hashed_password):
                    raise NotAuthorizedException("Invalid password")

            await mfa_service.disable_mfa(session=session, user=user)
            await session.commit()

        return {"message": "MFA disabled"}
