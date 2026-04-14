"""
Unified v2 auth endpoints — /api/v2/auth/*

Single namespace for all authentication flows:
- Local email/password login
- SSO via any OIDC provider (including external brokers)
- MFA verification
- Session management
- Provider discovery
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from logging import getLogger
from typing import Optional
from uuid import UUID, uuid4

from litestar import Controller, Response, delete, get, post
from litestar.connection import Request
from litestar.exceptions import (
    ClientException,
    NotAuthorizedException,
    NotFoundException,
)
from litestar.params import Parameter
from litestar.response import Redirect
from litestar.response.base import ASGIResponse
from litestar.security.jwt import Token
from pydantic import BaseModel, Field

from core.config.app import alchemy
from core.config.base import get_auth_settings
from middlewares.auth import Auth
from services.auth.identity_resolution import resolve_identity
from services.auth.provider_registry import get_provider, get_provider_names
from services.auth.session_service import create_access_token, create_session
from services.users import auth_service, mfa_service, refresh_token_service
from utils.cookies import clear_auth_cookies, set_auth_cookies, set_auth_cookies_asgi

logger = getLogger(__name__)


# --- Schemas ---


class LoginRequest(BaseModel):
    email: str = Field(..., max_length=320)
    password: str = Field(..., max_length=128)


class SignupRequest(BaseModel):
    email: str = Field(..., max_length=320)
    password: str = Field(..., min_length=8, max_length=128)
    name: Optional[str] = Field(None, max_length=255)


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


class MfaVerifyRequest(BaseModel):
    code: str = Field(..., description="6-digit TOTP code or 8-char backup code")


class MfaSetupResponse(BaseModel):
    secret: str
    provisioning_uri: str
    qr_code: str


class MfaConfirmRequest(BaseModel):
    secret: str
    totp_code: str = Field(..., min_length=6, max_length=6)


class MfaConfirmResponse(BaseModel):
    backup_codes: list[str]
    message: str = "MFA enabled successfully. Save your backup codes."


class MfaDisableRequest(BaseModel):
    password: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., max_length=320)


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


class ProviderInfo(BaseModel):
    name: str
    type: str  # 'oidc', 'oauth2'


# --- Controller ---


class AuthV2Controller(Controller):
    """Unified auth endpoints (v2).

    Single auth namespace for all flows.
    """

    path = "/auth"
    tags = ["Auth v2"]

    @staticmethod
    async def before_request(request: Request) -> None:  # type: ignore[override]
        from middlewares.rate_limit import check_rate_limit

        check_rate_limit(request)

    # ── Provider Discovery ──────────────────────────────────────────────

    @get("/providers", exclude_from_auth=True, summary="List enabled auth providers")
    async def list_providers(self) -> list[ProviderInfo]:
        """Return the list of enabled SSO providers for the login UI."""
        names = get_provider_names()
        result = []
        for name in names:
            ptype = "oauth2" if name == "github" else "oidc"
            result.append(ProviderInfo(name=name, type=ptype))
        return result

    # ── Local Auth ──────────────────────────────────────────────────────

    @post("/login", exclude_from_auth=True, summary="Login with email and password")
    async def login(self, data: LoginRequest, request: Request) -> Response:
        device_info = request.headers.get("user-agent")

        async with alchemy.get_session() as session:
            user = await auth_service.authenticate(
                session=session,
                email=data.email,
                password=data.password,
            )

            # Check if MFA is enabled
            if user.is_two_factor_enabled:
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
                    samesite="lax",
                    path="/api/v2/auth/mfa",
                    max_age=300,
                )
                return response

            # No MFA — create session
            internal_session = await create_session(
                session=session,
                user=user,
                device_info=device_info,
                auth_method="password",
            )
            await session.commit()

            response = Response(
                {
                    "access_token": internal_session.access_token,
                    "token_type": "bearer",
                    "user_id": str(user.id),
                    "email": user.email,
                },
            )
            set_auth_cookies(
                response, internal_session.access_token, internal_session.refresh_token
            )
            return response

    @post("/signup", exclude_from_auth=True, summary="Register a new local user")
    async def signup(self, data: SignupRequest) -> SignupResponse:
        async with alchemy.get_session() as session:
            user = await auth_service.signup(
                session=session,
                email=data.email,
                password=data.password,
                name=data.name,
            )
            await session.commit()
            return SignupResponse(user_id=str(user.id), email=user.email)

    # ── SSO (OIDC / OAuth2) ────────────────────────────────────────────

    @get(
        "/sso/{provider:str}",
        exclude_from_auth=True,
        summary="Start SSO login — redirect to IdP",
    )
    async def sso_start(self, provider: str, request: Request) -> ASGIResponse:
        """Redirect to the IdP's authorization page.

        Sets state and nonce cookies for validation on callback.
        """
        try:
            strategy = get_provider(provider)
        except KeyError:
            raise ClientException(f"Unknown provider: {provider}")

        # Capture return_to so we can redirect back after SSO callback
        return_to = request.query_params.get("return_to", "/admin")
        # Sanitize: only allow relative paths starting with /
        if not return_to.startswith("/"):
            return_to = "/admin"

        # Generate state (signed JWT for CSRF) and nonce
        settings = get_auth_settings()
        nonce = secrets.token_urlsafe(32)
        state_token = Token(
            sub=provider,
            exp=datetime.now(UTC) + timedelta(minutes=10),
            extras={"provider": provider, "return_to": return_to},
        )
        state = state_token.encode(
            secret=settings.SECRET_KEY,
            algorithm=settings.JWT_ENCRYPTION_ALGORITHM,
        )

        authorization_url = await strategy.get_authorization_url(
            state=state, nonce=nonce
        )

        response = Redirect(authorization_url)
        asgi_response = response.to_asgi_response(app=None, request=request)

        # Set state and nonce cookies
        asgi_response.headers.add(
            "Set-Cookie",
            f"sso_state={state}; Max-Age=600; Secure; HttpOnly; Path=/api/v2/auth/sso; SameSite=None;",
        )
        asgi_response.headers.add(
            "Set-Cookie",
            f"sso_nonce={nonce}; Max-Age=600; Secure; HttpOnly; Path=/api/v2/auth/sso; SameSite=None;",
        )
        return asgi_response

    async def _handle_sso_callback(
        self,
        provider: str,
        request: Request,
        code: str | None,
        oauth_state: str | None,
    ) -> ASGIResponse:
        """Shared logic for GET and POST SSO callbacks."""
        try:
            strategy = get_provider(provider)
        except KeyError:
            raise ClientException(f"Unknown provider: {provider}")

        settings = get_auth_settings()
        expected_state = request.cookies.get("sso_state")
        if not expected_state or not oauth_state:
            raise NotAuthorizedException("Missing SSO state")

        try:
            state_token = Token.decode(
                encoded_token=oauth_state,
                secret=settings.SECRET_KEY,
                algorithm=settings.JWT_ENCRYPTION_ALGORITHM,
            )
        except Exception:
            raise NotAuthorizedException("Invalid or expired SSO state token")

        if (state_token.extras or {}).get("provider") != provider:
            raise NotAuthorizedException("State token provider mismatch")

        if expected_state != oauth_state:
            raise NotAuthorizedException("SSO state mismatch")

        expected_nonce = request.cookies.get("sso_nonce")
        if not expected_nonce:
            raise NotAuthorizedException("Missing nonce cookie")

        try:
            identity = await strategy.handle_callback(
                request_data={"code": code},
                expected_nonce=expected_nonce,
            )
        except ValueError as e:
            logger.warning("SSO callback failed for %s: %s", provider, e)
            raise NotAuthorizedException(f"SSO authentication failed: {e}") from e

        device_info = request.headers.get("user-agent")
        async with alchemy.get_session() as session:
            user = await resolve_identity(session, identity)
            internal_session = await create_session(
                session=session,
                user=user,
                device_info=device_info,
                auth_method=f"sso:{provider}",
            )
            await session.commit()

        return_to = (state_token.extras or {}).get("return_to", "/admin")
        redirect_url = f"{settings.OAUTH2_REDIRECT_BASE_URL}{return_to}"
        response = Redirect(redirect_url)
        asgi_response = response.to_asgi_response(app=None, request=request)

        set_auth_cookies_asgi(
            asgi_response, internal_session.access_token, internal_session.refresh_token
        )
        asgi_response.headers.add(
            "Set-Cookie",
            "sso_state=; Max-Age=0; Secure; HttpOnly; Path=/api/v2/auth/sso; SameSite=Lax;",
        )
        asgi_response.headers.add(
            "Set-Cookie",
            "sso_nonce=; Max-Age=0; Secure; HttpOnly; Path=/api/v2/auth/sso; SameSite=Lax;",
        )
        return asgi_response

    @get(
        "/sso/{provider:str}/callback",
        exclude_from_auth=True,
        summary="SSO callback — complete authentication (query params)",
    )
    async def sso_callback(
        self,
        provider: str,
        request: Request,
        code: str | None = None,
        oauth_state: str | None = Parameter(default=None, query="state"),
    ) -> ASGIResponse:
        """Handle the IdP callback for providers using response_mode=query (GET)."""
        return await self._handle_sso_callback(provider, request, code, oauth_state)

    @post(
        "/sso/{provider:str}/callback",
        exclude_from_auth=True,
        opt={"exclude_from_csrf": True},
        summary="SSO callback — complete authentication (form_post)",
    )
    async def sso_callback_post(
        self,
        provider: str,
        request: Request,
    ) -> ASGIResponse:
        """Handle the IdP callback for providers using response_mode=form_post (POST).

        Microsoft Entra ID uses form_post — the browser POSTs code and state
        from an auto-submitted form. This endpoint is excluded from CSRF because
        the POST originates from the IdP, not from our frontend.
        """
        form = await request.form()
        code = form.get("code")
        oauth_state = form.get("state")
        return await self._handle_sso_callback(provider, request, code, oauth_state)

    # ── Token Refresh ──────────────────────────────────────────────────

    @post("/refresh", exclude_from_auth=True, summary="Refresh access token")
    async def refresh(self, request: Request) -> Response[RefreshResponse]:
        old_refresh_token = request.cookies.get("refresh_token")
        if not old_refresh_token:
            raise NotAuthorizedException("No refresh token provided")

        device_info = request.headers.get("user-agent")

        async with alchemy.get_session() as session:
            (
                new_refresh_plaintext,
                _,
                user_id,
            ) = await refresh_token_service.validate_and_rotate(
                session=session,
                plaintext_token=old_refresh_token,
                device_info=device_info,
            )

            from services.users.service import get_user_by_id

            user = await get_user_by_id(user_id)
            if not user:
                raise NotAuthorizedException("User not found")

            access_token = create_access_token(user, auth_method="refresh")
            await session.commit()

            response = Response(RefreshResponse(access_token=access_token))
            set_auth_cookies(response, access_token, new_refresh_plaintext)
            return response

    # ── Current User ───────────────────────────────────────────────────

    @get("/me", summary="Get current user info")
    async def me(self, request: Request) -> dict:
        auth: Auth = request.scope.get("auth")
        if not auth:
            raise NotAuthorizedException("Not authenticated")

        user = getattr(auth, "user", None)
        if user is not None:
            from services.auth.user_info import build_user_info

            return await build_user_info(user, auth)

        # Fallback: return raw token/API-key data
        return auth.data

    # ── Logout ─────────────────────────────────────────────────────────

    @post("/logout", exclude_from_auth=True, summary="Logout and revoke session")
    async def logout(self, request: Request) -> Response[dict]:
        refresh_token = request.cookies.get("refresh_token")
        if refresh_token:
            token_hash = refresh_token_service.hash_token(refresh_token)
            async with alchemy.get_session() as session:
                await refresh_token_service.revoke_token_family(session, token_hash)
                await session.commit()

        response = Response({"message": "Logged out"})
        clear_auth_cookies(response)
        return response

    # ── Sessions ───────────────────────────────────────────────────────

    @get("/sessions", summary="List active sessions")
    async def list_sessions(self, request: Request) -> list[SessionResponse]:
        auth: Auth = request.scope.get("auth")
        if not auth or not auth.user:
            raise NotAuthorizedException("Authentication required")

        async with alchemy.get_session() as session:
            tokens = await refresh_token_service.get_active_sessions(
                session=session, user_id=auth.user.id
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

    @delete("/sessions/{session_id:uuid}", summary="Revoke a session", status_code=200)
    async def revoke_session(self, session_id: UUID, request: Request) -> dict:
        auth: Auth = request.scope.get("auth")
        if not auth or not auth.user:
            raise NotAuthorizedException("Authentication required")

        async with alchemy.get_session() as session:
            revoked = await refresh_token_service.revoke_session_by_id(
                session=session, token_id=session_id, user_id=auth.user.id
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

    # ── MFA ────────────────────────────────────────────────────────────

    @get("/mfa/setup", summary="Begin MFA setup")
    async def mfa_setup(self, request: Request) -> MfaSetupResponse:
        auth: Auth = request.scope.get("auth")
        if not auth or not auth.user:
            raise NotAuthorizedException("Authentication required")
        if auth.user.is_two_factor_enabled:
            raise ClientException("MFA is already enabled")

        result = await mfa_service.setup_mfa(auth.user)
        return MfaSetupResponse(**result)

    @post("/mfa/confirm", summary="Confirm MFA setup with TOTP code")
    async def mfa_confirm(
        self, request: Request, data: MfaConfirmRequest
    ) -> MfaConfirmResponse:
        auth: Auth = request.scope.get("auth")
        if not auth or not auth.user:
            raise NotAuthorizedException("Authentication required")

        async with alchemy.get_session() as session:
            from core.domain.users.service import UsersService

            service = UsersService(session=session)
            user = await service.get(auth.user.id)
            backup_codes = await mfa_service.confirm_mfa_setup(
                session=session, user=user, secret=data.secret, totp_code=data.totp_code
            )
            await session.commit()

        return MfaConfirmResponse(backup_codes=backup_codes)

    @post("/mfa/verify", exclude_from_auth=True, summary="Verify MFA during login")
    async def mfa_verify(self, request: Request, data: MfaVerifyRequest) -> Response:
        mfa_cookie = request.cookies.get("mfa_challenge")
        if not mfa_cookie:
            raise NotAuthorizedException("MFA challenge not found — please login first")

        settings = get_auth_settings()
        try:
            token = Token.decode(
                encoded_token=mfa_cookie,
                secret=settings.SECRET_KEY,
                algorithm=settings.JWT_ENCRYPTION_ALGORITHM,
            )
        except Exception as e:
            raise NotAuthorizedException("Invalid or expired MFA challenge") from e

        extras = token.extras or {}
        if extras.get("purpose") != "mfa_challenge":
            raise NotAuthorizedException("Invalid token purpose")
        user_id = extras.get("user_id")
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

            internal_session = await create_session(
                session=session,
                user=user,
                device_info=request.headers.get("user-agent"),
                auth_method="password",
            )
            await session.commit()

        response = Response(
            {
                "access_token": internal_session.access_token,
                "token_type": "bearer",
                "user_id": str(user.id),
            },
        )
        set_auth_cookies(
            response, internal_session.access_token, internal_session.refresh_token
        )
        response.delete_cookie(key="mfa_challenge", path="/api/v2/auth/mfa")
        return response

    @delete("/mfa", summary="Disable MFA", status_code=200)
    async def mfa_disable(self, request: Request, data: MfaDisableRequest) -> dict:
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
                if not data.password:
                    raise NotAuthorizedException("Password required to disable MFA")
                from services.users.password import verify_password_async

                if not await verify_password_async(data.password, user.hashed_password):
                    raise NotAuthorizedException("Invalid password")

            await mfa_service.disable_mfa(session=session, user=user)
            await session.commit()

        return {"message": "MFA disabled"}

    # ── Password Management ────────────────────────────────────────────

    @post("/password/forgot", exclude_from_auth=True, summary="Request password reset")
    async def forgot_password(self, data: ForgotPasswordRequest) -> dict:
        # Always return success to prevent email enumeration
        logger.info("Password reset requested for %s", data.email)

        # Generate and store reset token
        async with alchemy.get_session() as session:
            from services.users.service import get_user_by_email

            user = await get_user_by_email(data.email)
            if user:
                import hashlib

                token_plaintext = secrets.token_urlsafe(32)
                token_hash = hashlib.sha256(token_plaintext.encode("utf-8")).hexdigest()

                from core.db.models.user.password_reset_token import PasswordResetToken

                reset_token = PasswordResetToken(
                    token_hash=token_hash,
                    user_id=user.id,
                    expires_at=datetime.now(UTC) + timedelta(hours=1),
                )
                session.add(reset_token)
                await session.commit()

                # EMAIL DELIVERY REQUIRED: The plaintext token must be sent
                # to the user via email. Integration with an email service
                # (SMTP, SendGrid, SES, etc.) is required to complete this flow.
                # The reset link format should be:
                #   {FRONTEND_URL}/auth/reset-password?token={token_plaintext}
                #
                # Until email delivery is implemented, password reset tokens
                # are created but not delivered. Admin can retrieve them from
                # the password_reset_token table for manual reset.
                logger.warning(
                    "Password reset token created for user %s but email delivery is not yet configured",
                    user.email,
                )

        return {"message": "If the email exists, a reset link has been sent."}

    @post(
        "/password/reset", exclude_from_auth=True, summary="Reset password with token"
    )
    async def reset_password(self, data: ResetPasswordRequest) -> dict:
        import hashlib

        from services.users.password import hash_password_async

        token_hash = hashlib.sha256(data.token.encode("utf-8")).hexdigest()

        async with alchemy.get_session() as session:
            from core.db.models.user.password_reset_token import PasswordResetToken
            from sqlalchemy import select

            stmt = select(PasswordResetToken).where(
                PasswordResetToken.token_hash == token_hash
            )
            result = await session.execute(stmt)
            reset_token = result.scalar_one_or_none()

            if not reset_token:
                raise NotAuthorizedException("Invalid or expired reset token")

            if reset_token.used_at is not None:
                raise NotAuthorizedException("Reset token already used")

            if reset_token.expires_at < datetime.now(UTC):
                raise NotAuthorizedException("Reset token expired")

            # Update password
            from core.domain.users.service import UsersService

            service = UsersService(session=session)
            user = await service.get(reset_token.user_id)
            await session.refresh(user, attribute_names=["hashed_password"])

            user.hashed_password = await hash_password_async(data.new_password)
            reset_token.used_at = datetime.now(UTC)

            # Revoke all sessions for security
            await refresh_token_service.revoke_all_user_sessions(
                session=session, user_id=user.id
            )

            await session.commit()

        return {
            "message": "Password has been reset. Please login with your new password."
        }
