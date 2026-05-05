"""OAuth 2.1 authorization-server provider for the Magnet MCP server.

Implements the `OAuthAuthorizationServerProvider` Protocol from the MCP Python
SDK, backed by Magnet's existing user / refresh-token tables plus the new
oauth_client / oauth_authorization_code tables.

The flow:

  1. Client → /authorize  (SDK validates client + PKCE + redirect_uri)
        → calls our `authorize()` → returns URL to /api/v2/auth/mcp_authorize
  2. Browser → /api/v2/auth/mcp_authorize?pending=<jwt>
        → if logged in: `issue_authorization_code()` mints code, 302s to client
        → if not: redirects through Microsoft / Google / local SSO and back
  3. Client → /token (code + PKCE verifier)
        → SDK calls `load_authorization_code()` then `exchange_authorization_code()`
        → we mint an HS256 JWT with `aud=<MCP_AUDIENCE>` + a refresh-token row
  4. Client → /mcp with `Authorization: Bearer <token>`
        → SDK's bearer middleware calls our `load_access_token()`
        → we decode the JWT and require `aud == MCP_AUDIENCE`
  5. Client → /token (grant_type=refresh_token)
        → SDK calls `load_refresh_token()` then `exchange_refresh_token()`
        → we rotate via the existing refresh_token_service (preserves family + audience)

Token signing: reuses Magnet's HS256 SECRET_KEY. Web-app session tokens have
no `aud` claim; MCP tokens are stamped with `aud == MCP_AUDIENCE`. The
audience check is enforced both at /api routes (middlewares/auth.py) and at
/mcp (here, in `load_access_token`).
"""

from __future__ import annotations

import hashlib
import secrets
import time
from datetime import UTC, datetime
from logging import getLogger
from typing import TYPE_CHECKING
from urllib.parse import quote

from litestar.security.jwt import Token
from mcp.server.auth.provider import (
    AccessToken,
    AuthorizationCode,
    OAuthAuthorizationServerProvider,
    RefreshToken,
    construct_redirect_uri,
)
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken
from sqlalchemy import select

from core.config.app import alchemy
from core.config.base import get_auth_settings, get_mcp_settings
from core.db.models.oauth import OAuthAuthorizationCode, OAuthClient
from core.db.models.user.refresh_token import RefreshToken as DBRefreshToken
from services.auth.session_service import create_access_token
from services.users import refresh_token_service
from services.users.refresh_token_service import (
    create_refresh_token,
    hash_token,
    revoke_token_family,
)

from .pending_state import encode_pending_state

if TYPE_CHECKING:
    from mcp.server.auth.provider import AuthorizationParams

logger = getLogger(__name__)


def _hash_code(code: str) -> str:
    """SHA-256 of an authorization code (we never store plaintext)."""
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def _is_loopback(uri: str) -> bool:
    """RFC 8252 §7.3 — loopback redirect URIs match across ports.

    Returns True when `uri` uses http://127.0.0.1 or http://localhost on any
    port. This lets local CLIs and MCP Inspector pick ephemeral ports without
    re-registering the redirect URI on every dev run.
    """
    from urllib.parse import urlparse

    parsed = urlparse(uri)
    if parsed.scheme != "http":
        return False
    return parsed.hostname in ("127.0.0.1", "localhost")


def _redirect_uri_allowed(client: OAuthClient, requested: str) -> bool:
    """Exact-match against client.redirect_uris, with RFC 8252 loopback exception."""
    if requested in client.redirect_uris:
        return True
    if _is_loopback(requested):
        from urllib.parse import urlparse

        req_host = urlparse(requested).hostname
        for allowed in client.redirect_uris:
            allowed_parsed = urlparse(allowed)
            if allowed_parsed.scheme == "http" and allowed_parsed.hostname == req_host:
                return True
    return False


def _client_to_oauth_info(client: OAuthClient) -> OAuthClientInformationFull:
    """Translate our DB row into the SDK's pydantic client info object."""
    return OAuthClientInformationFull(
        client_id=client.client_id,
        client_name=client.name,
        redirect_uris=client.redirect_uris,
        token_endpoint_auth_method=(
            "none" if client.is_public else "client_secret_post"
        ),
        grant_types=["authorization_code", "refresh_token"],
        response_types=["code"],
    )


class MagnetOAuthProvider(
    OAuthAuthorizationServerProvider[AuthorizationCode, RefreshToken, AccessToken]
):
    """OAuth 2.1 AS provider for Magnet's MCP server."""

    # ------------------------------------------------------------------ Clients

    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
        async with alchemy.get_session() as session:
            stmt = select(OAuthClient).where(
                OAuthClient.client_id == client_id,
                OAuthClient.enabled.is_(True),
            )
            result = await session.execute(stmt)
            client = result.scalar_one_or_none()
            if client is None:
                return None
            return _client_to_oauth_info(client)

    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        # Dynamic Client Registration is intentionally disabled — clients are
        # onboarded via the admin panel or a seed migration. See
        # docs/MCP_CONNECTOR_SETUP.md for the rationale.
        raise NotImplementedError("Dynamic Client Registration is not enabled")

    # ------------------------------------------------------------------ /authorize

    async def authorize(
        self,
        client: OAuthClientInformationFull,
        params: "AuthorizationParams",
    ) -> str:
        """Build the URL the SDK should 302 the user-agent to.

        Tighter validation than what the SDK already did:
          * redirect_uri whitelisted on the OAuth client row in DB (loopback OK)
          * MCP_AUDIENCE matches the requested resource (if provided)
        """
        async with alchemy.get_session() as session:
            stmt = select(OAuthClient).where(
                OAuthClient.client_id == client.client_id,
                OAuthClient.enabled.is_(True),
            )
            db_client = (await session.execute(stmt)).scalar_one_or_none()
            if db_client is None:
                # Should never happen — get_client() was already called by SDK.
                raise ValueError("Client disappeared between get_client and authorize")

            redirect_str = str(params.redirect_uri)
            if not _redirect_uri_allowed(db_client, redirect_str):
                # Mirror the SDK's behavior on validation failures.
                from mcp.server.auth.provider import AuthorizeError

                raise AuthorizeError(
                    error="invalid_request",
                    error_description=(
                        f"redirect_uri '{redirect_str}' is not registered for "
                        f"client '{client.client_id}'"
                    ),
                )

        # Build pending-state JWT carrying everything we need to finalize.
        pending = encode_pending_state(client_id=client.client_id, params=params)

        # Hand control to Magnet's user-facing login + finalize endpoint.
        # MCP_ISSUER_URL is the public origin of the AS (which is Magnet).
        mcp_settings = get_mcp_settings()
        return (
            f"{mcp_settings.MCP_ISSUER_URL.rstrip('/')}"
            f"/api/v2/auth/mcp_authorize?pending={quote(pending, safe='')}"
        )

    # ------------------------------------------------------------------ /token (code)

    async def load_authorization_code(
        self,
        client: OAuthClientInformationFull,
        authorization_code: str,
    ) -> AuthorizationCode | None:
        async with alchemy.get_session() as session:
            stmt = select(OAuthAuthorizationCode).where(
                OAuthAuthorizationCode.code_hash == _hash_code(authorization_code)
            )
            row = (await session.execute(stmt)).scalar_one_or_none()
            if row is None:
                return None
            if row.consumed_at is not None:
                # Single-use enforcement. The SDK reports invalid_grant.
                return None
            if row.client_id != client.client_id:
                return None
            return AuthorizationCode(
                code=authorization_code,
                scopes=row.scope.split(" ") if row.scope else [],
                expires_at=row.expires_at.timestamp(),
                client_id=row.client_id,
                code_challenge=row.code_challenge,
                redirect_uri=row.redirect_uri,
                redirect_uri_provided_explicitly=row.redirect_uri_provided_explicitly,
                resource=row.resource,
            )

    async def exchange_authorization_code(
        self,
        client: OAuthClientInformationFull,
        authorization_code: AuthorizationCode,
    ) -> OAuthToken:
        """Consume the code and mint access + refresh tokens.

        SDK has already verified PKCE, redirect_uri match, expiry, client match.
        """
        from mcp.server.auth.provider import TokenError

        from services.users.service import get_user_by_id

        mcp_settings = get_mcp_settings()
        auth_settings = get_auth_settings()
        audience = mcp_settings.MCP_AUDIENCE

        async with alchemy.get_session() as session:
            stmt = select(OAuthAuthorizationCode).where(
                OAuthAuthorizationCode.code_hash == _hash_code(authorization_code.code)
            )
            row = (await session.execute(stmt)).scalar_one_or_none()
            if row is None or row.consumed_at is not None:
                raise TokenError(
                    error="invalid_grant",
                    error_description="authorization code does not exist",
                )
            row.consumed_at = datetime.now(UTC)
            user_id = row.user_id
            client_id_for_session = row.client_id

            user = await get_user_by_id(user_id)
            if user is None:
                raise TokenError(
                    error="invalid_grant",
                    error_description="user not found",
                )

            access_token = create_access_token(
                user, auth_method=f"oauth:{client_id_for_session}", audience=audience
            )
            refresh_plaintext, _ = await create_refresh_token(
                session=session,
                user_id=user_id,
                device_info=f"oauth:{client_id_for_session}",
                client_id=client_id_for_session,
                audience=audience,
            )
            await session.commit()

        return OAuthToken(
            access_token=access_token,
            token_type="Bearer",
            expires_in=auth_settings.ACCESS_TOKEN_EXPIRATION_MINUTES * 60,
            refresh_token=refresh_plaintext,
            scope=" ".join(authorization_code.scopes)
            if authorization_code.scopes
            else None,
        )

    # ------------------------------------------------------------------ /token (refresh)

    async def load_refresh_token(
        self,
        client: OAuthClientInformationFull,
        refresh_token: str,
    ) -> RefreshToken | None:
        token_hash = hash_token(refresh_token)
        async with alchemy.get_session() as session:
            stmt = select(DBRefreshToken).where(
                DBRefreshToken.token_hash == token_hash,
            )
            row = (await session.execute(stmt)).scalar_one_or_none()
            if row is None:
                return None
            if row.revoked_at is not None:
                return None
            if row.client_id != client.client_id:
                return None
            return RefreshToken(
                token=refresh_token,
                client_id=row.client_id or client.client_id,
                scopes=[],
                expires_at=int(row.expires_at.timestamp()) if row.expires_at else None,
            )

    async def exchange_refresh_token(
        self,
        client: OAuthClientInformationFull,
        refresh_token: RefreshToken,
        scopes: list[str],
    ) -> OAuthToken:
        """Rotate the refresh token (reuse-detection family logic) and mint a new access token."""
        from mcp.server.auth.provider import TokenError

        from services.users.service import get_user_by_id

        auth_settings = get_auth_settings()
        mcp_settings = get_mcp_settings()
        audience = mcp_settings.MCP_AUDIENCE

        async with alchemy.get_session() as session:
            try:
                (
                    new_refresh_plaintext,
                    new_db_token,
                    user_id,
                ) = await refresh_token_service.validate_and_rotate(
                    session=session,
                    plaintext_token=refresh_token.token,
                    device_info=f"oauth:{client.client_id}",
                )
            except Exception as e:
                raise TokenError(
                    error="invalid_grant",
                    error_description=str(e),
                )

            # validate_and_rotate already preserves client_id + audience on the
            # new row, but defensively belt-and-suspenders here in case a row
            # pre-dates the client_id/audience columns:
            if new_db_token.client_id is None:
                new_db_token.client_id = client.client_id
            if new_db_token.audience is None:
                new_db_token.audience = audience

            user = await get_user_by_id(user_id)
            if user is None:
                raise TokenError(
                    error="invalid_grant",
                    error_description="user not found",
                )

            access_token = create_access_token(
                user, auth_method=f"oauth:{client.client_id}:refresh", audience=audience
            )
            await session.commit()

        return OAuthToken(
            access_token=access_token,
            token_type="Bearer",
            expires_in=auth_settings.ACCESS_TOKEN_EXPIRATION_MINUTES * 60,
            refresh_token=new_refresh_plaintext,
            scope=" ".join(scopes) if scopes else None,
        )

    # ------------------------------------------------------------------ Bearer auth

    async def load_access_token(self, token: str) -> AccessToken | None:
        """Verify a bearer token presented at /mcp.

        Audience binding (RFC 8707): rejects any token whose `aud` claim does
        not match MCP_AUDIENCE. This is what stops a stolen web-app cookie
        from working at /mcp.
        """
        auth_settings = get_auth_settings()
        mcp_settings = get_mcp_settings()
        if not auth_settings.SECRET_KEY:
            return None

        try:
            decoded = Token.decode(
                encoded_token=token,
                secret=auth_settings.SECRET_KEY,
                algorithm=auth_settings.JWT_ENCRYPTION_ALGORITHM,
            )
        except Exception:
            return None

        if decoded.aud != mcp_settings.MCP_AUDIENCE:
            return None

        extras = decoded.extras or {}
        return AccessToken(
            token=token,
            client_id=extras.get("auth_method", "").removeprefix("oauth:").split(":")[0]
            or "claude",
            scopes=extras.get("roles", []) or [],
            expires_at=int(decoded.exp.timestamp()) if decoded.exp else None,
            resource=mcp_settings.MCP_AUDIENCE,
        )

    # ------------------------------------------------------------------ Revocation

    async def revoke_token(
        self,
        token: AccessToken | RefreshToken,
    ) -> None:
        """Revoke the entire family that issued this token.

        Per OAuth 2.1, revocation should affect both access and refresh tokens.
        Magnet's family-based model already gives this for free: revoking the
        family invalidates all tokens (access + refresh) issued from it.
        """
        # Only RefreshToken carries enough info to find a family; AccessToken
        # revocation is a no-op (let it expire naturally).
        if not isinstance(token, RefreshToken):
            return

        token_hash = hash_token(token.token)
        async with alchemy.get_session() as session:
            await revoke_token_family(session, token_hash)
            await session.commit()


# Helper used by the auth_v2 mcp_authorize endpoint to finalize the flow once
# the user is authenticated.
async def issue_authorization_code(
    *,
    user_id,
    client_id: str,
    redirect_uri: str,
    redirect_uri_provided_explicitly: bool,
    code_challenge: str,
    scopes: list[str],
    resource: str | None,
    state: str | None,
) -> str:
    """Mint a fresh OAuth authorization code, persist it, return the redirect URL.

    Returns: full URL to redirect the browser to (client_redirect_uri?code=&state=).
    """
    from datetime import timedelta

    mcp_settings = get_mcp_settings()
    code_plaintext = secrets.token_urlsafe(48)
    code_hash = _hash_code(code_plaintext)
    expires_at = datetime.now(UTC) + timedelta(
        seconds=mcp_settings.MCP_AUTH_CODE_TTL_SECONDS
    )

    async with alchemy.get_session() as session:
        row = OAuthAuthorizationCode(
            code_hash=code_hash,
            client_id=client_id,
            user_id=user_id,
            redirect_uri=redirect_uri,
            redirect_uri_provided_explicitly=redirect_uri_provided_explicitly,
            code_challenge=code_challenge,
            scope=" ".join(scopes) if scopes else None,
            resource=resource,
            expires_at=expires_at,
        )
        session.add(row)
        await session.commit()

    # construct_redirect_uri is the SDK's URL-builder — preserves existing
    # query params on the redirect URI and appends ours.
    return construct_redirect_uri(redirect_uri, code=code_plaintext, state=state)


# Singleton instance — referenced by both the FastMCP wiring and the
# auth_v2 mcp_authorize endpoint.
provider = MagnetOAuthProvider()


__all__ = [
    "MagnetOAuthProvider",
    "issue_authorization_code",
    "provider",
]


# Suppress unused-import linter on the helper imports.
_ = (time,)
