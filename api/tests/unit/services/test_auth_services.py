"""
Unit tests for the unified auth services.

Tests identity resolution, session service, provider registry,
and strategy implementations.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from core.exceptions import ConflictError
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
                JWT_ISSUER="magnet-ai",
                JWT_AUDIENCE="magnet-ai-api",
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


# --- Refresh Token Service ---


class _ScalarResult:
    """Result of session.execute() returning a single scalar value."""

    def __init__(self, value=None):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class _RefreshTokenSession:
    """Async session double for refresh-token tests.

    Supports a queued sequence of execute() responses, so tests can
    distinguish between the FOR UPDATE SELECT, the active-token-in-family
    probe, and the family-revoke UPDATE.
    """

    def __init__(self, responses: list | None = None, execute_exception=None):
        self._responses = list(responses or [])
        self.execute_exception = execute_exception
        self.executed = []
        self.added = []

    async def execute(self, statement):
        self.executed.append(statement)
        if self.execute_exception is not None:
            exc = self.execute_exception
            self.execute_exception = None
            raise exc
        if not self._responses:
            return _ScalarResult(None)
        next_value = self._responses.pop(0)
        if isinstance(next_value, BaseException):
            raise next_value
        return _ScalarResult(next_value)

    def add(self, token):
        self.added.append(token)


def _make_lock_not_available_error():
    from sqlalchemy.exc import OperationalError

    class _PgLockOrig(Exception):
        pgcode = "55P03"

    return OperationalError(
        "SELECT 1",
        {},
        _PgLockOrig("could not obtain lock on row"),
    )


class TestRefreshTokenService:
    @pytest.mark.anyio
    async def test_validate_and_rotate_lock_contention_is_retryable(self):
        from services.users.refresh_token_service import validate_and_rotate

        session = _RefreshTokenSession(
            execute_exception=_make_lock_not_available_error()
        )

        with pytest.raises(ConflictError, match="validation in progress"):
            await validate_and_rotate(session, "refresh-token")

    @pytest.mark.anyio
    async def test_validate_and_rotate_unexpected_db_error_is_not_retryable(self):
        from sqlalchemy.exc import OperationalError

        from services.users.refresh_token_service import validate_and_rotate

        unrelated = OperationalError("SELECT 1", {}, Exception("connection reset"))
        session = _RefreshTokenSession(execute_exception=unrelated)

        with pytest.raises(OperationalError):
            await validate_and_rotate(session, "refresh-token")

    @pytest.mark.anyio
    async def test_validate_and_rotate_recently_rotated_with_active_sibling_is_retryable(
        self,
    ):
        from core.db.models.user.refresh_token import RefreshToken
        from services.users.refresh_token_service import hash_token, validate_and_rotate

        token = RefreshToken(
            token_hash=hash_token("old-refresh-token"),
            family_id=uuid4(),
            user_id=uuid4(),
            expires_at=datetime.now(UTC) + timedelta(days=1),
            revoked_at=datetime.now(UTC),
        )
        # Sequence: FOR UPDATE → revoked token; active-sibling probe → some id
        session = _RefreshTokenSession(responses=[token, uuid4()])

        with patch(
            "services.users.refresh_token_service.get_auth_settings"
        ) as mock_settings:
            mock_settings.return_value = MagicMock(
                REFRESH_TOKEN_REUSE_GRACE_SECONDS=5,
                REFRESH_TOKEN_EXPIRATION_DAYS=7,
            )

            with pytest.raises(ConflictError, match="already rotated"):
                await validate_and_rotate(session, "old-refresh-token")

        # Benign rotation race must not insert a new token nor revoke family
        assert session.added == []
        # Two SELECTs and no UPDATE issued
        assert len(session.executed) == 2

    @pytest.mark.anyio
    async def test_validate_and_rotate_revoked_without_active_sibling_revokes_family(
        self,
    ):
        from core.db.models.user.refresh_token import RefreshToken
        from services.users.refresh_token_service import hash_token, validate_and_rotate

        from core.exceptions import AuthError

        token = RefreshToken(
            token_hash=hash_token("old-refresh-token"),
            family_id=uuid4(),
            user_id=uuid4(),
            expires_at=datetime.now(UTC) + timedelta(days=1),
            revoked_at=datetime.now(UTC),
        )
        # Sequence: FOR UPDATE → revoked token; active-sibling probe → None
        # (family already revoked); UPDATE family-revoke → no-op response
        session = _RefreshTokenSession(responses=[token, None, None])

        with patch(
            "services.users.refresh_token_service.get_auth_settings"
        ) as mock_settings:
            mock_settings.return_value = MagicMock(
                REFRESH_TOKEN_REUSE_GRACE_SECONDS=5,
                REFRESH_TOKEN_EXPIRATION_DAYS=7,
            )

            with pytest.raises(AuthError, match="reuse detected"):
                await validate_and_rotate(session, "old-refresh-token")

        # Family-revoke UPDATE must have been issued (3 statements total)
        assert len(session.executed) == 3
        assert session.added == []

    @pytest.mark.anyio
    async def test_validate_and_rotate_after_grace_window_revokes_family(self):
        from core.db.models.user.refresh_token import RefreshToken
        from services.users.refresh_token_service import hash_token, validate_and_rotate

        from core.exceptions import AuthError

        revoked_long_ago = datetime.now(UTC) - timedelta(seconds=60)
        token = RefreshToken(
            token_hash=hash_token("old-refresh-token"),
            family_id=uuid4(),
            user_id=uuid4(),
            expires_at=datetime.now(UTC) + timedelta(days=1),
            revoked_at=revoked_long_ago,
        )
        # Even if a sibling appears active, grace window has expired so
        # the active-sibling probe must NOT be reached — only the family
        # revoke UPDATE follows the FOR UPDATE SELECT.
        session = _RefreshTokenSession(responses=[token, None])

        with patch(
            "services.users.refresh_token_service.get_auth_settings"
        ) as mock_settings:
            mock_settings.return_value = MagicMock(
                REFRESH_TOKEN_REUSE_GRACE_SECONDS=5,
                REFRESH_TOKEN_EXPIRATION_DAYS=7,
            )

            with pytest.raises(AuthError, match="reuse detected"):
                await validate_and_rotate(session, "old-refresh-token")

        assert session.added == []

    @pytest.mark.anyio
    async def test_validate_and_rotate_active_token_does_not_enter_grace_branch(self):
        from core.db.models.user.refresh_token import RefreshToken
        from services.users.refresh_token_service import hash_token, validate_and_rotate

        token = RefreshToken(
            token_hash=hash_token("active-token"),
            family_id=uuid4(),
            user_id=uuid4(),
            expires_at=datetime.now(UTC) + timedelta(days=1),
            revoked_at=None,
        )
        session = _RefreshTokenSession(responses=[token])

        with patch(
            "services.users.refresh_token_service.get_auth_settings"
        ) as mock_settings:
            mock_settings.return_value = MagicMock(
                REFRESH_TOKEN_REUSE_GRACE_SECONDS=5,
                REFRESH_TOKEN_EXPIRATION_DAYS=7,
            )

            new_plaintext, new_db_token, user_id = await validate_and_rotate(
                session, "active-token"
            )

        assert isinstance(new_plaintext, str) and new_plaintext
        assert user_id == token.user_id
        assert token.revoked_at is not None
        assert session.added == [new_db_token]
        # Only the FOR UPDATE SELECT — no active-sibling probe, no family revoke
        assert len(session.executed) == 1


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


# --- API key middleware ---


class TestApiKeyAuth:
    def _patch_config(self, **kwargs):
        from services.api_keys.types import ApiKeyConfigPersisted

        defaults = dict(
            id="api-key-id",
            name="test-key",
            created_at=datetime.now(UTC),
            value_masked="...abcd",
            hash="hash",
            is_active=True,
            expires_at=None,
        )
        defaults.update(kwargs)
        return ApiKeyConfigPersisted(**defaults)

    def test_active_key_returns_auth(self):
        from middlewares.auth import ensure_request_auth_data_api_key

        with patch("middlewares.auth.get_api_key_config") as mock_get:
            mock_get.return_value = self._patch_config()
            auth = ensure_request_auth_data_api_key("plaintext", None)

        assert auth.type == "api_key"
        assert auth.data["api_client_code"] == "test-key"

    def test_expired_key_is_rejected(self):
        from litestar.exceptions import NotAuthorizedException

        from middlewares.auth import ensure_request_auth_data_api_key

        expired_at = datetime.now(UTC) - timedelta(seconds=1)
        with patch("middlewares.auth.get_api_key_config") as mock_get:
            mock_get.return_value = self._patch_config(expires_at=expired_at)

            with pytest.raises(NotAuthorizedException, match="expired"):
                ensure_request_auth_data_api_key("plaintext", None)

    def test_inactive_key_is_rejected(self):
        from litestar.exceptions import NotAuthorizedException

        from middlewares.auth import ensure_request_auth_data_api_key

        with patch("middlewares.auth.get_api_key_config") as mock_get:
            mock_get.return_value = self._patch_config(is_active=False)

            with pytest.raises(NotAuthorizedException, match="inactive"):
                ensure_request_auth_data_api_key("plaintext", None)


# --- Auth settings validation ---


class TestAuthSettingsValidation:
    def test_short_secret_key_rejected(self):
        from utils.cookies import validate_auth_settings

        with patch("utils.cookies.get_auth_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                AUTH_ENABLED=True,
                SECRET_KEY="short",
                AUTH_COOKIE_SAMESITE="lax",
                AUTH_COOKIE_SECURE=True,
            )
            with pytest.raises(ValueError, match="SECRET_KEY"):
                validate_auth_settings()

    def test_samesite_none_without_secure_rejected(self):
        from utils.cookies import validate_auth_settings

        with patch("utils.cookies.get_auth_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                AUTH_ENABLED=True,
                SECRET_KEY="x" * 64,
                AUTH_COOKIE_SAMESITE="none",
                AUTH_COOKIE_SECURE=False,
            )
            with pytest.raises(ValueError, match="AUTH_COOKIE_SAMESITE=none"):
                validate_auth_settings()

    def test_signing_key_must_differ_from_encryption_key(self, monkeypatch):
        from utils.cookies import validate_auth_settings

        shared = "x" * 64
        monkeypatch.setenv("SECRET_ENCRYPTION_KEY", shared)
        with patch("utils.cookies.get_auth_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                AUTH_ENABLED=True,
                SECRET_KEY=shared,
                AUTH_COOKIE_SAMESITE="lax",
                AUTH_COOKIE_SECURE=True,
            )
            with pytest.raises(ValueError, match="must differ"):
                validate_auth_settings()

    def test_disabled_auth_skips_validation(self):
        from utils.cookies import validate_auth_settings

        with patch("utils.cookies.get_auth_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                AUTH_ENABLED=False,
                SECRET_KEY="",
                AUTH_COOKIE_SAMESITE="none",
                AUTH_COOKIE_SECURE=False,
            )
            validate_auth_settings()  # should not raise


# --- CORS origin validation ---


class TestCorsOriginValidation:
    def test_wildcard_rejected(self):
        from core.server.plugins.cors import _validate_origin

        assert _validate_origin("*") is None

    def test_path_rejected(self):
        from core.server.plugins.cors import _validate_origin

        assert _validate_origin("https://example.com/path") is None

    def test_no_scheme_rejected(self):
        from core.server.plugins.cors import _validate_origin

        assert _validate_origin("example.com") is None

    def test_valid_origin_normalized(self):
        from core.server.plugins.cors import _validate_origin

        assert _validate_origin("https://app.example.com/") == "https://app.example.com"
        assert _validate_origin("  http://localhost:5173  ") == "http://localhost:5173"


# --- Signup enumeration defence ---


class TestSignupEnumeration:
    @pytest.mark.anyio
    async def test_duplicate_email_returns_none(self):
        from services.users import auth_service

        existing_user = MagicMock(id=uuid4(), email="dup@example.com")

        class _Service:
            def __init__(self, session):
                self._existing = existing_user

            async def get_one_or_none(self, **_kwargs):
                return self._existing

        with (
            patch("services.users.auth_service.UsersService", _Service),
            patch(
                "services.users.auth_service.hash_password_async",
                return_value="hashed",
            ),
        ):
            result = await auth_service.signup(
                session=MagicMock(),
                email="dup@example.com",
                password="hunter2hunter2",
            )

        assert result is None  # no ConflictError raised, no user created


# --- Bootstrap superuser ---


class _StubScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class _BootstrapSession:
    """Async session stand-in for bootstrap tests.

    Returns queued scalar values for `execute()` calls (admin role lookup,
    existing UserRole lookup) and tracks `add()` invocations.
    """

    def __init__(self, scalar_responses):
        self._responses = list(scalar_responses)
        self.added = []
        self.execute_calls = 0

    async def execute(self, _stmt):
        self.execute_calls += 1
        if not self._responses:
            return _StubScalarResult(None)
        return _StubScalarResult(self._responses.pop(0))

    def add(self, obj):
        self.added.append(obj)


class TestBootstrapSuperuser:
    @pytest.mark.anyio
    async def test_creates_user_when_missing(self):
        from services.users.bootstrap import bootstrap_superuser

        admin_role = MagicMock(id=uuid4())
        session = _BootstrapSession(
            scalar_responses=[admin_role, None],  # role exists, no UserRole yet
        )

        new_user = MagicMock(id=uuid4(), email="boot@example.com")

        class _Service:
            def __init__(self, *_args, **_kwargs):
                pass

            async def get_one_or_none(self, **_kwargs):
                return None

            async def create(self, user, auto_commit=False):
                new_user.email = user.email
                return new_user

        with (
            patch("services.users.bootstrap.UsersService", _Service),
            patch(
                "services.users.bootstrap.hash_password_async",
                return_value="hashed",
            ),
        ):
            result = await bootstrap_superuser(
                session,
                email="boot@example.com",
                password="strong-password-1234",
                name="Boot Admin",
            )

        assert result.created is True
        assert result.role_assigned is True
        assert result.email == "boot@example.com"
        # Exactly one UserRole was added — for the admin role.
        assert len(session.added) == 1

    @pytest.mark.anyio
    async def test_promotes_existing_user_and_assigns_role(self):
        from services.users.bootstrap import bootstrap_superuser

        admin_role = MagicMock(id=uuid4())
        existing_user = MagicMock(
            id=uuid4(),
            email="user@example.com",
            is_superuser=False,
            is_active=False,
            is_verified=False,
            name=None,
            hashed_password="old-hash",
        )
        session = _BootstrapSession(scalar_responses=[admin_role, None])

        update_calls = []

        class _Service:
            def __init__(self, *_args, **_kwargs):
                pass

            async def get_one_or_none(self, **_kwargs):
                return existing_user

            async def update(self, user, auto_commit=False):
                update_calls.append(user)
                return user

        with (
            patch("services.users.bootstrap.UsersService", _Service),
            patch(
                "services.users.bootstrap.hash_password_async",
                return_value="new-hash",
            ),
        ):
            result = await bootstrap_superuser(
                session,
                email="user@example.com",
                password="strong-password-1234",
            )

        assert result.created is False
        assert result.updated is True
        assert result.role_assigned is True
        assert existing_user.is_superuser is True
        assert existing_user.is_active is True
        assert existing_user.is_verified is True
        # reset_password=False by default — old hash kept
        assert existing_user.hashed_password == "old-hash"
        assert len(update_calls) == 1

    @pytest.mark.anyio
    async def test_no_op_when_already_superuser_with_role(self):
        from services.users.bootstrap import bootstrap_superuser

        admin_role = MagicMock(id=uuid4())
        # NOTE: `name=` in the MagicMock constructor sets the mock's display
        # name, not an attribute. Set `.name` after construction.
        existing_user = MagicMock(
            id=uuid4(),
            email="admin@example.com",
            is_superuser=True,
            is_active=True,
            is_verified=True,
            hashed_password="kept",
        )
        existing_user.name = "Admin"
        existing_user_role = MagicMock(id=uuid4())
        session = _BootstrapSession(
            scalar_responses=[admin_role, existing_user_role],
        )

        update_calls = []

        class _Service:
            def __init__(self, *_args, **_kwargs):
                pass

            async def get_one_or_none(self, **_kwargs):
                return existing_user

            async def update(self, user, auto_commit=False):
                update_calls.append(user)
                return user

        with (
            patch("services.users.bootstrap.UsersService", _Service),
            patch(
                "services.users.bootstrap.hash_password_async",
                return_value="should-not-be-called",
            ),
        ):
            result = await bootstrap_superuser(
                session,
                email="admin@example.com",
                password="strong-password-1234",
                name="Admin",
            )

        assert result.created is False
        assert result.updated is False
        assert result.role_assigned is False
        assert update_calls == []
        assert session.added == []
        assert existing_user.hashed_password == "kept"

    @pytest.mark.anyio
    async def test_reset_password_replaces_hash_for_existing_user(self):
        from services.users.bootstrap import bootstrap_superuser

        admin_role = MagicMock(id=uuid4())
        existing_user_role = MagicMock(id=uuid4())
        existing_user = MagicMock(
            id=uuid4(),
            email="admin@example.com",
            is_superuser=True,
            is_active=True,
            is_verified=True,
            hashed_password="old-hash",
        )
        existing_user.name = "Admin"
        session = _BootstrapSession(
            scalar_responses=[admin_role, existing_user_role],
        )

        class _Service:
            def __init__(self, *_args, **_kwargs):
                pass

            async def get_one_or_none(self, **_kwargs):
                return existing_user

            async def update(self, user, auto_commit=False):
                return user

        with (
            patch("services.users.bootstrap.UsersService", _Service),
            patch(
                "services.users.bootstrap.hash_password_async",
                return_value="rotated-hash",
            ),
        ):
            result = await bootstrap_superuser(
                session,
                email="admin@example.com",
                password="rotated-password-1234",
                reset_password=True,
            )

        assert result.updated is True
        assert existing_user.hashed_password == "rotated-hash"
