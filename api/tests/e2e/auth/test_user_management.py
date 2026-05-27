"""Tests for admin user-creation and self-service password change.

Two endpoints added on the alpha line:

- ``POST /api/admin/users``            — a ``manage:users`` holder (superuser or
  tenant admin) creates a regular, non-superuser account.
- ``POST /api/v2/auth/password/change`` — an authenticated user rotates their
  own password without email confirmation; all *other* sessions are revoked.

Testing strategy (two layers):

1. **Behaviour** — invoke the handler coroutine *directly* in the test's own
   event loop, with ``alchemy.get_session()`` rebound to the shared per-test
   ``db_session``. This sidesteps the cross-event-loop quirk that ``AsyncTestClient``
   introduces (it runs the app via an anyio portal in a *separate* loop, so an
   asyncpg connection opened in the test loop can't be driven from the handler
   loop — see the note in ``tests/e2e/auth/test_rbac.py``). Everything runs in
   the single rolled-back transaction, so writes are asserted *and* isolated.

2. **Auth boundary** — drive the real router + auth middleware + guards over
   HTTP with signed JWTs to prove the endpoints are wired and gated correctly
   (anonymous → 401, ``user`` role lacks ``manage:users`` → 403). These cases
   never reach the handler body, so the cross-loop / pollution concerns above
   don't apply.
"""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from litestar import Litestar
from litestar.exceptions import ClientException, NotAuthorizedException
from litestar.plugins.problem_details import (
    ProblemDetailsConfig,
    ProblemDetailsPlugin,
)
from litestar.plugins.sqlalchemy import AsyncSessionConfig, SQLAlchemyAsyncConfig
from litestar.security.jwt import Token
from litestar.testing import AsyncTestClient

from core.exceptions import ConflictError
from routes.admin.users import UsersController, UserCreateRequest
from routes.auth_v2 import AuthV2Controller, ChangePasswordRequest

# Raw handler coroutines (unwrapped from the litestar route handlers). `self`
# is unused by both, so we pass ``None``.
_create_user = UsersController.create_user.fn
_change_password = AuthV2Controller.change_password.fn


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


class _SharedSessionAlchemy:
    """Stand-in for ``core.config.app.alchemy`` that hands handlers the
    per-test ``db_session`` instead of opening a fresh connection.

    The session is owned by the ``db_session`` fixture, so the context manager
    intentionally does NOT close it. Handler ``await session.commit()`` lands on
    the savepoint-joined test session, leaving the outer (rolled-back)
    transaction intact.
    """

    def __init__(self, session):
        self._session = session

    def get_session(self):
        session = self._session

        @asynccontextmanager
        async def _cm():
            yield session

        return _cm()


async def _seed_system_roles(session) -> None:
    """Insert the ``admin`` / ``user`` system roles the handlers rely on."""
    from sqlalchemy import select

    from core.db.models.user.role import Role

    for slug, name in (("admin", "Admin"), ("user", "User")):
        existing = (
            await session.execute(select(Role).where(Role.slug == slug))
        ).scalar_one_or_none()
        if existing is None:
            session.add(Role(slug=slug, name=name, is_system=True, tenant_id=None))
    await session.flush()


async def _make_user(
    db_session,
    tenant_id,
    *,
    email: str | None = None,
    is_superuser: bool = False,
    role_slugs: list[str] | None = None,
    password: str | None = None,
):
    """Create a User (+ role assignments, + optional hashed password)."""
    from sqlalchemy import select

    from core.db.models.user.role import Role
    from core.db.models.user.user import User
    from core.db.models.user.user_role import UserRole
    from services.users.password import hash_password_async

    user = User(
        email=email or f"um-{uuid4().hex[:8]}@test.magnet.ai",
        name="UM Test",
        is_active=True,
        is_verified=True,
        is_superuser=is_superuser,
        tenant_id=tenant_id,
        hashed_password=(await hash_password_async(password)) if password else None,
    )
    db_session.add(user)
    await db_session.flush()

    for slug in role_slugs or []:
        role = (
            await db_session.execute(select(Role).where(Role.slug == slug))
        ).scalar_one_or_none()
        if role is not None:
            db_session.add(
                UserRole(
                    user_id=user.id,
                    role_id=role.id,
                    tenant_id=tenant_id,
                    assigned_at=datetime.now(UTC),
                )
            )
    await db_session.flush()
    return user


class _FakeRequest:
    """Minimal stand-in for litestar's Request used by the two handlers.

    The handlers only read ``request.scope['auth']`` and ``request.cookies``.
    """

    def __init__(self, auth, cookies: dict | None = None):
        self.scope = {"auth": auth}
        self.cookies = cookies or {}


# ---------------------------------------------------------------------------
# Behaviour layer — direct handler invocation against the shared session
# ---------------------------------------------------------------------------


@pytest.fixture
def behaviour_env(db_session, monkeypatch):
    """Rebind ``alchemy`` on both route modules to the shared test session."""
    shared = _SharedSessionAlchemy(db_session)
    import routes.admin.users as admin_users
    import routes.auth_v2 as auth_v2

    monkeypatch.setattr(admin_users, "alchemy", shared)
    monkeypatch.setattr(auth_v2, "alchemy", shared)
    return shared


@pytest.mark.integration
class TestAdminCreateUserBehaviour:
    async def test_superuser_creates_regular_user(
        self, behaviour_env, db_session, default_tenant
    ):
        await _seed_system_roles(db_session)
        su = await _make_user(db_session, default_tenant.id, is_superuser=True)
        auth = SimpleNamespace(user=su, tenant_id=str(default_tenant.id))

        email = f"created-{uuid4().hex[:8]}@test.magnet.ai"
        result = await _create_user(
            None,
            _FakeRequest(auth),
            UserCreateRequest(email=email, password="Created-Pass-123", name="Created"),
        )

        assert result.email == email
        assert result.is_superuser is False
        assert result.is_verified is True
        assert result.roles == ["user"]

        from sqlalchemy import select

        from core.db.models.user.user import User

        created = (
            await db_session.execute(select(User).where(User.email == email))
        ).scalar_one()
        assert created.tenant_id == default_tenant.id
        assert created.is_superuser is False
        await db_session.refresh(created, attribute_names=["hashed_password"])
        assert created.hashed_password  # password was hashed + stored

    async def test_duplicate_email_conflicts(
        self, behaviour_env, db_session, default_tenant
    ):
        await _seed_system_roles(db_session)
        su = await _make_user(db_session, default_tenant.id, is_superuser=True)
        auth = SimpleNamespace(user=su, tenant_id=str(default_tenant.id))
        email = f"dup-{uuid4().hex[:8]}@test.magnet.ai"

        await _create_user(
            None,
            _FakeRequest(auth),
            UserCreateRequest(email=email, password="Dup-Pass-12345"),
        )

        with pytest.raises(ConflictError):
            await _create_user(
                None,
                _FakeRequest(auth),
                UserCreateRequest(email=email, password="Dup-Pass-67890"),
            )

    async def test_created_user_is_in_caller_tenant(
        self, behaviour_env, db_session, default_tenant
    ):
        """A second tenant's admin creates a user in *their* tenant, not default."""
        from core.db.models.tenant.tenant import Tenant

        await _seed_system_roles(db_session)
        other = Tenant(slug=f"other-{uuid4().hex[:6]}", name="Other")
        db_session.add(other)
        await db_session.flush()

        su = await _make_user(db_session, other.id, is_superuser=True)
        auth = SimpleNamespace(user=su, tenant_id=str(other.id))

        email = f"tenant-{uuid4().hex[:8]}@test.magnet.ai"
        result = await _create_user(
            None,
            _FakeRequest(auth),
            UserCreateRequest(email=email, password="Tenant-Pass-1"),
        )
        assert result.email == email

        from sqlalchemy import select

        from core.db.models.user.user import User

        created = (
            await db_session.execute(select(User).where(User.email == email))
        ).scalar_one()
        assert created.tenant_id == other.id


@pytest.mark.integration
class TestPasswordChangeBehaviour:
    async def test_change_succeeds_and_rotates_hash(
        self, behaviour_env, db_session, default_tenant
    ):
        old, new = "Old-Pass-123456", "New-Pass-789012"
        user = await _make_user(db_session, default_tenant.id, password=old)
        auth = SimpleNamespace(user=user)

        result = await _change_password(
            None,
            _FakeRequest(auth),
            ChangePasswordRequest(current_password=old, new_password=new),
        )
        assert result == {"message": "Password changed successfully"}

        from sqlalchemy import select

        from core.db.models.user.user import User
        from services.users.password import verify_password_async

        refreshed = (
            await db_session.execute(select(User).where(User.id == user.id))
        ).scalar_one()
        await db_session.refresh(refreshed, attribute_names=["hashed_password"])
        assert await verify_password_async(new, refreshed.hashed_password)
        assert not await verify_password_async(old, refreshed.hashed_password)

    async def test_wrong_current_password_rejected(
        self, behaviour_env, db_session, default_tenant
    ):
        user = await _make_user(db_session, default_tenant.id, password="Right-Pass-1")
        auth = SimpleNamespace(user=user)

        with pytest.raises(NotAuthorizedException):
            await _change_password(
                None,
                _FakeRequest(auth),
                ChangePasswordRequest(
                    current_password="wrong-one", new_password="Another-Pass-1"
                ),
            )

    async def test_same_password_rejected(
        self, behaviour_env, db_session, default_tenant
    ):
        pw = "Same-Pass-12345"
        user = await _make_user(db_session, default_tenant.id, password=pw)
        auth = SimpleNamespace(user=user)

        with pytest.raises(ClientException):
            await _change_password(
                None,
                _FakeRequest(auth),
                ChangePasswordRequest(current_password=pw, new_password=pw),
            )

    async def test_account_without_local_password_rejected(
        self, behaviour_env, db_session, default_tenant
    ):
        """SSO-only account (no hashed_password) cannot use password change."""
        user = await _make_user(db_session, default_tenant.id, password=None)
        auth = SimpleNamespace(user=user)

        with pytest.raises(ClientException):
            await _change_password(
                None,
                _FakeRequest(auth),
                ChangePasswordRequest(
                    current_password="whatever", new_password="New-Pass-123"
                ),
            )

    async def test_other_sessions_revoked_current_kept(
        self, behaviour_env, db_session, default_tenant
    ):
        old, new = "Multi-Old-12345", "Multi-New-67890"
        user = await _make_user(db_session, default_tenant.id, password=old)

        from services.users import refresh_token_service

        current_plain, current_tok = await refresh_token_service.create_refresh_token(
            db_session, user.id, tenant_id=default_tenant.id, device_info="current"
        )
        _, other_tok = await refresh_token_service.create_refresh_token(
            db_session, user.id, tenant_id=default_tenant.id, device_info="other"
        )
        await db_session.flush()

        auth = SimpleNamespace(user=user)
        result = await _change_password(
            None,
            _FakeRequest(auth, cookies={"refresh_token": current_plain}),
            ChangePasswordRequest(current_password=old, new_password=new),
        )
        assert result == {"message": "Password changed successfully"}

        await db_session.refresh(current_tok)
        await db_session.refresh(other_tok)
        assert current_tok.revoked_at is None, "current session should stay active"
        assert other_tok.revoked_at is not None, "other session should be revoked"


# ---------------------------------------------------------------------------
# Auth-boundary layer — real router + middleware + guards over HTTP
# ---------------------------------------------------------------------------


@pytest.fixture
async def um_app(engine, db_session, monkeypatch):
    """Auth-enabled app for boundary/guard assertions (no handler-body writes)."""
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-jwt-signing-32+chars")
    monkeypatch.setenv("JWT_ENCRYPTION_ALGORITHM", "HS256")
    monkeypatch.setenv("JWT_ISSUER", "magnet-test")
    monkeypatch.setenv("JWT_AUDIENCE", "magnet-test-api")

    from core.config.base import get_auth_settings, get_settings

    get_auth_settings.cache_clear()
    get_settings.cache_clear()

    await _seed_system_roles(db_session)

    di_config = SQLAlchemyAsyncConfig(
        engine_instance=engine,
        before_send_handler="autocommit",
        session_config=AsyncSessionConfig(expire_on_commit=False),
    )

    # Resolve the principal via the per-test session so the user's roles are
    # visible to the guards (mirrors tests/e2e/auth/test_rbac.py).
    from sqlalchemy import select
    from sqlalchemy.orm import joinedload, selectinload

    import services.users.service as users_service
    from core.db.models.user.user import User

    async def _test_get_user_by_id(user_id):
        stmt = (
            select(User)
            .where(User.id == uuid.UUID(str(user_id)))
            .options(joinedload(User.tenant), selectinload(User.roles))
        )
        result = await db_session.execute(stmt)
        return result.scalar_one_or_none()

    monkeypatch.setattr(users_service, "get_user_by_id", _test_get_user_by_id)

    import middlewares.auth as auth_middleware
    from middlewares.auth import ensure_request_auth_data_local_jwt as _real_local_jwt

    async def _wrapped_local_jwt(token_str):
        auth = await _real_local_jwt(token_str)
        if auth is None:
            return None
        s = get_auth_settings()
        try:
            tok = Token.decode(
                encoded_token=token_str,
                secret=s.SECRET_KEY,
                algorithm=s.JWT_ENCRYPTION_ALGORITHM,
                audience=s.JWT_AUDIENCE or None,
                issuer=s.JWT_ISSUER or None,
            )
        except Exception:
            return auth
        if (tid := (tok.extras or {}).get("tenant_id")) is not None:
            auth.data["tenant_id"] = tid
        return auth

    monkeypatch.setattr(
        auth_middleware, "ensure_request_auth_data_local_jwt", _wrapped_local_jwt
    )

    from core.server.plugins import DependenciesPlugin
    from guards.permissions import reset_role_permissions_cache
    from middlewares.auth import create_auth_middleware
    from routes import get_route_handlers

    reset_role_permissions_cache()  # use SYSTEM_ROLE_DEFAULTS fallback

    app = Litestar(
        route_handlers=get_route_handlers(auth_enabled=True, web_included=False),
        debug=True,
        middleware=[create_auth_middleware()],
        plugins=[
            SQLAlchemyPlugin(config=di_config),
            ProblemDetailsPlugin(
                config=ProblemDetailsConfig(enable_for_all_http_exceptions=True)
            ),
            DependenciesPlugin(),
        ],
    )

    yield app

    reset_role_permissions_cache()
    get_auth_settings.cache_clear()
    get_settings.cache_clear()


@pytest.fixture
async def um_client(um_app) -> AsyncTestClient:
    async with AsyncTestClient(app=um_app) as c:
        yield c


def _mint_jwt(user, *, role_slugs: list[str], is_superuser: bool = False) -> str:
    from core.config.base import get_auth_settings

    settings = get_auth_settings()
    extras = {
        "user_id": str(user.id),
        "is_superuser": is_superuser,
        "is_verified": True,
        "auth_method": "password",
        "roles": role_slugs,
    }
    if getattr(user, "tenant_id", None):
        extras["tenant_id"] = str(user.tenant_id)
    token = Token(
        sub=user.email,
        exp=datetime.now(UTC) + timedelta(minutes=15),
        jti=str(uuid.uuid4()),
        iss=settings.JWT_ISSUER or None,
        aud=settings.JWT_AUDIENCE or None,
        extras=extras,
    )
    return token.encode(
        secret=settings.SECRET_KEY, algorithm=settings.JWT_ENCRYPTION_ALGORITHM
    )


@pytest.mark.e2e
class TestAdminCreateUserBoundary:
    async def test_anonymous_rejected(self, um_client):
        resp = await um_client.post(
            "/api/admin/users",
            json={"email": "anon@test.magnet.ai", "password": "Anon-Pass-123"},
        )
        assert resp.status_code in (401, 403), resp.text

    async def test_plain_user_forbidden(self, um_client, db_session, default_tenant):
        """A ``user``-role principal lacks ``manage:users`` → 403."""
        user = await _make_user(db_session, default_tenant.id, role_slugs=["user"])
        headers = {"Authorization": f"Bearer {_mint_jwt(user, role_slugs=['user'])}"}
        resp = await um_client.post(
            "/api/admin/users",
            headers=headers,
            json={
                "email": f"x-{uuid4().hex[:8]}@test.magnet.ai",
                "password": "Pw-1234567",
            },
        )
        assert resp.status_code == 403, resp.text


@pytest.mark.e2e
class TestPasswordChangeBoundary:
    async def test_anonymous_rejected(self, um_client):
        resp = await um_client.post(
            "/api/v2/auth/password/change",
            json={"current_password": "a", "new_password": "bbbbbbbb"},
        )
        assert resp.status_code in (401, 403), resp.text
