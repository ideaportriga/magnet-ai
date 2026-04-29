"""Signed JWT carrying OAuth /authorize state across the SSO redirect chain.

Why: when a client hits `/authorize`, the SDK calls our `authorize()` and
expects a URL string. We bounce the user to `/api/v2/auth/mcp_authorize`,
which may need to redirect through Microsoft Entra (or another IdP) before
producing an authorization code. That round-trip needs to carry the
client_id, redirect_uri, code_challenge, scope, resource, and CSRF state
back to us — encoded into a short-lived signed JWT so we don't need a
DB row for every in-flight authorize.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from uuid import uuid4

from litestar.security.jwt import Token

from core.config.base import get_auth_settings, get_mcp_settings

if TYPE_CHECKING:
    from mcp.server.auth.provider import AuthorizationParams


_PURPOSE = "mcp_pending_authorize"


def encode_pending_state(
    *,
    client_id: str,
    params: "AuthorizationParams",
) -> str:
    """Sign a JWT capturing everything needed to finalize the /authorize flow."""
    auth_settings = get_auth_settings()
    mcp_settings = get_mcp_settings()

    extras = {
        "purpose": _PURPOSE,
        "client_id": client_id,
        "redirect_uri": str(params.redirect_uri),
        "redirect_uri_provided_explicitly": params.redirect_uri_provided_explicitly,
        "code_challenge": params.code_challenge,
        "scopes": params.scopes or [],
        "resource": params.resource,
        "state": params.state,
    }
    token = Token(
        sub=client_id,
        exp=datetime.now(UTC)
        + timedelta(seconds=mcp_settings.MCP_PENDING_STATE_TTL_SECONDS),
        jti=str(uuid4()),
        extras=extras,
    )
    return token.encode(
        secret=auth_settings.SECRET_KEY,
        algorithm=auth_settings.JWT_ENCRYPTION_ALGORITHM,
    )


def decode_pending_state(jwt_string: str) -> dict:
    """Decode and validate the pending-state JWT.

    Returns the extras dict.
    Raises Exception (Token.decode error) if invalid/expired/wrong-purpose.
    """
    auth_settings = get_auth_settings()
    token = Token.decode(
        encoded_token=jwt_string,
        secret=auth_settings.SECRET_KEY,
        algorithm=auth_settings.JWT_ENCRYPTION_ALGORITHM,
    )
    extras = token.extras or {}
    if extras.get("purpose") != _PURPOSE:
        raise ValueError("Invalid pending-state token purpose")
    return extras
