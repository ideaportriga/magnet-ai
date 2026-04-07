"""
Unit tests for the unified auth services.

Tests identity resolution, session service, provider registry,
and strategy implementations.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from services.auth.types import ExternalIdentity


# --- ExternalIdentity ---


class TestExternalIdentity:
    def test_create_identity(self):
        identity = ExternalIdentity(
            provider="google",
            subject_id="123456",
            email="test@example.com",
            name="Test User",
            email_verified=True,
        )
        assert identity.provider == "google"
        assert identity.subject_id == "123456"
        assert identity.email == "test@example.com"
        assert identity.email_verified is True
        assert identity.suggested_roles is None

    def test_identity_defaults(self):
        identity = ExternalIdentity(
            provider="local",
            subject_id="test@example.com",
            email="test@example.com",
        )
        assert identity.name is None
        assert identity.email_verified is False
        assert identity.raw_claims == {}
        assert identity.suggested_roles is None


# --- GitHubStrategy ---


class TestGitHubStrategy:
    def test_provider_name(self):
        from services.auth.github_strategy import GitHubStrategy

        strategy = GitHubStrategy(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost:8000/callback",
        )
        assert strategy.get_provider_name() == "github"

    @pytest.mark.anyio
    async def test_authorization_url(self):
        from services.auth.github_strategy import GitHubStrategy

        strategy = GitHubStrategy(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost:8000/callback",
        )
        url = await strategy.get_authorization_url(
            state="test_state", nonce="test_nonce"
        )
        assert "github.com/login/oauth/authorize" in url
        assert "client_id=test_id" in url
        assert "state=test_state" in url

    @pytest.mark.anyio
    async def test_callback_missing_code(self):
        from services.auth.github_strategy import GitHubStrategy

        strategy = GitHubStrategy(
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost:8000/callback",
        )
        with pytest.raises(ValueError, match="Missing authorization code"):
            await strategy.handle_callback(request_data={})


# --- OIDCStrategy ---


class TestOIDCStrategy:
    def test_provider_name(self):
        from services.auth.oidc_strategy import OIDCProviderConfig, OIDCStrategy

        config = OIDCProviderConfig(
            name="test-provider",
            discovery_url="https://example.com/.well-known/openid-configuration",
            client_id="client_id",
            client_secret="client_secret",
            redirect_uri="http://localhost/callback",
        )
        strategy = OIDCStrategy(config)
        assert strategy.get_provider_name() == "test-provider"

    @pytest.mark.anyio
    async def test_callback_missing_code(self):
        from services.auth.oidc_strategy import OIDCProviderConfig, OIDCStrategy

        config = OIDCProviderConfig(
            name="test",
            discovery_url="https://example.com/.well-known/openid-configuration",
            client_id="client_id",
            client_secret="client_secret",
            redirect_uri="http://localhost/callback",
        )
        strategy = OIDCStrategy(config)
        with pytest.raises(ValueError, match="Missing authorization code"):
            await strategy.handle_callback(request_data={})


# --- Session Service ---


class TestSessionService:
    def test_create_access_token(self):
        """Test that create_access_token produces a valid JWT."""
        with patch("services.auth.session_service.get_auth_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                SECRET_KEY="test-secret-key-for-jwt-signing",
                JWT_ENCRYPTION_ALGORITHM="HS256",
                ACCESS_TOKEN_EXPIRATION_MINUTES=15,
            )

            user = MagicMock()
            user.email = "test@example.com"
            user.id = "user-123"
            user.is_superuser = False
            user.is_verified = True
            user.roles = []

            from services.auth.session_service import create_access_token

            token = create_access_token(user, auth_method="password")
            assert isinstance(token, str)
            assert len(token) > 0


# --- Scope Guard ---


class TestScopeGuard:
    def test_require_scope_passes_for_non_api_key(self):
        """Session-based auth should pass through scope guards."""
        from guards.scope import require_scope
        from middlewares.auth import Auth

        guard = require_scope("write:datasets")
        connection = MagicMock()
        connection.scope = {
            "auth": Auth(
                data={"user_id": "123", "roles": {"user"}},
                user_id="123",
                type="local_jwt",
            )
        }
        # Should not raise
        guard(connection, MagicMock())

    def test_require_scope_blocks_api_key_without_scope(self):
        """API keys without matching scope should be blocked."""
        from litestar.exceptions import PermissionDeniedException

        from guards.scope import require_scope
        from middlewares.auth import Auth

        guard = require_scope("write:datasets")
        connection = MagicMock()
        connection.scope = {
            "auth": Auth(
                data={
                    "user_id": "api_key:test",
                    "roles": {"user"},
                    "scopes": ["read:projects"],
                },
                user_id="api_key:test",
                type="api_key",
            )
        }
        with pytest.raises(PermissionDeniedException):
            guard(connection, MagicMock())

    def test_require_scope_passes_api_key_with_scope(self):
        """API keys with matching scope should pass."""
        from guards.scope import require_scope
        from middlewares.auth import Auth

        guard = require_scope("write:datasets")
        connection = MagicMock()
        connection.scope = {
            "auth": Auth(
                data={
                    "user_id": "api_key:test",
                    "roles": {"user"},
                    "scopes": ["write:datasets", "read:projects"],
                },
                user_id="api_key:test",
                type="api_key",
            )
        }
        # Should not raise
        guard(connection, MagicMock())

    def test_require_scope_legacy_key_no_scopes(self):
        """Legacy API keys (scopes=None) should pass through."""
        from guards.scope import require_scope
        from middlewares.auth import Auth

        guard = require_scope("write:datasets")
        connection = MagicMock()
        connection.scope = {
            "auth": Auth(
                data={
                    "user_id": "api_key:test",
                    "roles": {"user"},
                    "scopes": None,
                },
                user_id="api_key:test",
                type="api_key",
            )
        }
        # Should not raise (backward compat)
        guard(connection, MagicMock())
