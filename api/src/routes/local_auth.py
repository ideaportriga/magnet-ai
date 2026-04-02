"""Local authentication endpoints — signup, login, refresh, sessions, password reset.

These endpoints are for email+password authentication (local JWT).
OIDC endpoints remain in routes/auth.py.
"""

from __future__ import annotations

from datetime import datetime
from logging import getLogger
from typing import Optional
from uuid import UUID

from litestar import Controller, Response, delete, get, post
from litestar.connection import Request
from litestar.exceptions import NotAuthorizedException, NotFoundException
from pydantic import BaseModel, Field

from core.config.app import alchemy
from middlewares.auth import Auth
from services.users import auth_service
from services.users import refresh_token_service

logger = getLogger(__name__)


# --- Request/Response schemas ---


class SignupRequest(BaseModel):
    email: str = Field(..., max_length=320)
    password: str = Field(..., min_length=8, max_length=128)
    name: Optional[str] = Field(None, max_length=255)


class LoginRequest(BaseModel):
    email: str = Field(..., max_length=320)
    password: str = Field(..., max_length=128)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str


class SignupResponse(BaseModel):
    user_id: str
    email: str
    message: str = "Account created. Please verify your email."


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SessionResponse(BaseModel):
    id: UUID
    device_info: Optional[str]
    created_at: datetime
    expires_at: datetime


class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., max_length=320)


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


# --- Controller ---


class LocalAuthController(Controller):
    path = "/auth"
    tags = ["Auth"]

    @post("/signup", exclude_from_auth=True, summary="Register a new local user")
    async def signup(self, data: SignupRequest) -> SignupResponse:
        async with alchemy.get_session() as session:
            try:
                user = await auth_service.signup(
                    session=session,
                    email=data.email,
                    password=data.password,
                    name=data.name,
                )
                await session.commit()
            except ValueError as e:
                raise NotAuthorizedException(str(e)) from e

            return SignupResponse(
                user_id=str(user.id),
                email=user.email,
            )

    @post("/login", exclude_from_auth=True, summary="Login with email and password")
    async def login(self, data: LoginRequest, request: Request) -> Response:
        device_info = request.headers.get("user-agent")

        async with alchemy.get_session() as session:
            # First authenticate (verify credentials)
            try:
                user = await auth_service.authenticate(
                    session=session,
                    email=data.email,
                    password=data.password,
                )
            except ValueError as e:
                raise NotAuthorizedException(str(e)) from e

            # Check if MFA is enabled
            if user.is_two_factor_enabled:
                # Return MFA challenge instead of tokens
                from datetime import UTC, datetime, timedelta
                from uuid import uuid4

                from litestar.security.jwt import Token

                from core.config.base import get_auth_settings

                settings = get_auth_settings()
                mfa_token = Token(
                    sub=user.email,
                    exp=datetime.now(UTC) + timedelta(minutes=5),
                    jti=str(uuid4()),
                    extras={"user_id": str(user.id), "purpose": "mfa_challenge"},
                )
                mfa_jwt = mfa_token.encode(
                    secret=settings.SECRET_KEY,
                    algorithm=settings.JWT_ENCRYPTION_ALGORITHM,
                )

                await session.commit()

                response = Response(
                    {"mfa_required": True, "message": "MFA verification required"},
                )
                response.set_cookie(
                    key="mfa_challenge",
                    value=mfa_jwt,
                    httponly=True,
                    secure=True,
                    samesite="none",
                    path="/api/auth/mfa",
                    max_age=300,  # 5 minutes
                )
                return response

            # No MFA — issue tokens directly
            access_token = auth_service.create_access_token(
                user, auth_method="password"
            )

            refresh_plaintext, _ = await refresh_token_service.create_refresh_token(
                session=session,
                user_id=user.id,
                device_info=device_info,
            )

            await session.commit()

            response = Response(
                LoginResponse(
                    access_token=access_token,
                    user_id=str(user.id),
                    email=user.email,
                ),
            )

            # Set refresh token as HttpOnly cookie
            response.set_cookie(
                key="refresh_token",
                value=refresh_plaintext,
                httponly=True,
                secure=True,
                samesite="none",
                path="/",
                max_age=259200,  # 3 days
            )
            # Also set access token as cookie for consistency with OIDC flow
            response.set_cookie(
                key="token",
                value=access_token,
                httponly=True,
                secure=True,
                samesite="none",
                path="/",
                max_age=3600,  # 1 hour
            )

            return response

    @post("/refresh", exclude_from_auth=True, summary="Refresh access token")
    async def refresh(self, request: Request) -> Response[RefreshResponse]:
        old_refresh_token = request.cookies.get("refresh_token")
        if not old_refresh_token:
            raise NotAuthorizedException("No refresh token provided")

        device_info = request.headers.get("user-agent")

        async with alchemy.get_session() as session:
            try:
                (
                    new_refresh_plaintext,
                    _,
                    user_id,
                ) = await refresh_token_service.validate_and_rotate(
                    session=session,
                    plaintext_token=old_refresh_token,
                    device_info=device_info,
                )
            except ValueError as e:
                raise NotAuthorizedException(str(e)) from e

            # Load user for access token creation
            from services.users.service import get_user_by_id

            user = await get_user_by_id(user_id)
            if not user:
                raise NotAuthorizedException("User not found")

            access_token = auth_service.create_access_token(user, auth_method="refresh")

            await session.commit()

            response = Response(
                RefreshResponse(access_token=access_token),
            )
            response.set_cookie(
                key="refresh_token",
                value=new_refresh_plaintext,
                httponly=True,
                secure=True,
                samesite="none",
                path="/",
                max_age=259200,  # 3 days
            )
            response.set_cookie(
                key="token",
                value=access_token,
                httponly=True,
                secure=True,
                samesite="none",
                path="/",
                max_age=3600,  # 1 hour
            )
            return response

    @get("/sessions", summary="List active sessions")
    async def list_sessions(self, request: Request) -> list[SessionResponse]:
        auth: Auth = request.scope.get("auth")
        if not auth or not auth.user:
            raise NotAuthorizedException("Authentication required")

        async with alchemy.get_session() as session:
            tokens = await refresh_token_service.get_active_sessions(
                session=session,
                user_id=auth.user.id,
            )
            return [
                SessionResponse(
                    id=t.id,
                    device_info=t.device_info,
                    created_at=t.created_at,
                    expires_at=t.expires_at,
                )
                for t in tokens
            ]

    @delete(
        "/sessions/{session_id:uuid}",
        summary="Revoke a specific session",
        status_code=200,
    )
    async def revoke_session(self, session_id: UUID, request: Request) -> dict:
        auth: Auth = request.scope.get("auth")
        if not auth or not auth.user:
            raise NotAuthorizedException("Authentication required")

        async with alchemy.get_session() as session:
            revoked = await refresh_token_service.revoke_session_by_id(
                session=session,
                token_id=session_id,
                user_id=auth.user.id,
            )
            if not revoked:
                raise NotFoundException("Session not found")
            await session.commit()
            return {"message": "Session revoked"}

    @delete("/sessions", summary="Revoke all sessions except current", status_code=200)
    async def revoke_all_sessions(self, request: Request) -> dict:
        auth: Auth = request.scope.get("auth")
        if not auth or not auth.user:
            raise NotAuthorizedException("Authentication required")

        current_refresh = request.cookies.get("refresh_token")
        current_hash = None
        if current_refresh:
            current_hash = refresh_token_service.hash_token(current_refresh)

        async with alchemy.get_session() as session:
            count = await refresh_token_service.revoke_all_user_sessions(
                session=session,
                user_id=auth.user.id,
                except_token_hash=current_hash,
            )
            await session.commit()
            return {"message": f"Revoked {count} sessions"}

    @post("/forgot-password", exclude_from_auth=True, summary="Request password reset")
    async def forgot_password(self, data: ForgotPasswordRequest) -> dict:
        # Always return success to prevent email enumeration
        # In production, this would send an email with a reset link
        logger.info("Password reset requested")
        return {"message": "If the email exists, a reset link has been sent."}

    @post(
        "/reset-password", exclude_from_auth=True, summary="Reset password with token"
    )
    async def reset_password(self, data: ResetPasswordRequest) -> dict:
        # TODO: implement token validation and password reset in Phase 3 completion
        # For now, placeholder that validates the structure
        logger.info("Password reset attempted with token")
        return {"message": "Password reset functionality will be available soon."}
