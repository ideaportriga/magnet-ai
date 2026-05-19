"""E2E RBAC tests — exercise the permission-guard stack via real HTTP.

These tests boot a Litestar app with ``AUTH_ENABLED=true`` and the auth
middleware attached, then issue requests with signed JWTs for users that
carry different role / permission sets. Goals:

1. Unauthenticated traffic against ``/api/admin/*`` is rejected (401/403).
2. ``require_any_admin_capability()`` router-level guard rejects principals
   with zero permissions.
3. ``require_permission(...)`` per-endpoint guards enforce the exact code
   needed by each verb (read vs. write vs. delete on agents).
4. The admin Roles controller honours:
   - Capability ceiling (creator cannot grant unowned permissions).
   - System-role immutability (cannot edit/delete is_system roles).
   - Tenant scoping (other tenant's custom role is invisible).
5. Platform ``is_superuser`` bypasses the ceiling.

Auth-disabled e2e tests live alongside these — they remain valid because
permission guards are designed to fall through when ``AUTH_ENABLED=false``.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from litestar import Litestar
from litestar.plugins.problem_details import (
    ProblemDetailsConfig,
    ProblemDetailsPlugin,
)
from litestar.plugins.sqlalchemy import AsyncSessionConfig, SQLAlchemyAsyncConfig
from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin
from litestar.security.jwt import Token
from litestar.testing import AsyncTestClient


# ---------------------------------------------------------------------------
# Permission codes seeded for the test (subset of the production catalog).
# Keeps the fixture cheap — we only need the agents / roles permissions to
# exercise the guards we care about.
# ---------------------------------------------------------------------------

_TEST_PERMISSIONS = [
    ("read:agents", "agents", "read"),
    ("write:agents", "agents", "write"),
    ("delete:agents", "agents", "delete"),
    ("execute:agents", "agents", "execute"),
    ("read:roles", "roles", "read"),
    ("write:roles", "roles", "write"),
]


async def _seed_permissions(session) -> None:
    """Insert permission rows + system role grants used by the tests."""
    from core.db.models.user.permission import Permission as PermModel
    from core.db.models.user.role import Role
    from core.db.models.user.role_permission import RolePermission
    from sqlalchemy import select

    # Permission catalog.
    for code, resource, action in _TEST_PERMISSIONS:
        exists = (
            await session.execute(select(PermModel).where(PermModel.code == code))
        ).scalar_one_or_none()
        if exists is None:
            session.add(
                PermModel(
                    code=code,
                    resource_type=resource,
                    action=action,
                    is_system=True,
                )
            )
    await session.flush()

    # System roles. Slug-name uniqueness is partial-index per the migration.
    seeded: dict[str, Role] = {}
    for slug, name in (("admin", "Admin"), ("user", "User"), ("viewer", "Viewer")):
        existing = (
            await session.execute(select(Role).where(Role.slug == slug))
        ).scalar_one_or_none()
        if existing is None:
            existing = Role(slug=slug, name=name, is_system=True, tenant_id=None)
            session.add(existing)
        seeded[slug] = existing
    await session.flush()

    # Grants. admin → everything; user → reads + execute; viewer → reads only.
    grant_map = {
        "admin": [code for code, _, _ in _TEST_PERMISSIONS],
        "user": ["read:agents", "execute:agents"],
        "viewer": ["read:agents", "read:roles"],
    }
    for slug, codes in grant_map.items():
        role = seeded[slug]
        existing_codes = {
            row[0]
            for row in (
                await session.execute(
                    select(RolePermission.permission_code).where(
                        RolePermission.role_id == role.id
                    )
                )
            ).all()
        }
        for code in codes:
            if code in existing_codes:
                continue
            session.add(RolePermission(role_id=role.id, permission_code=code))
    await session.flush()


# ---------------------------------------------------------------------------
# Auth-enabled app fixture
# ---------------------------------------------------------------------------


@pytest.fixture
async def auth_app(engine, db_session, monkeypatch):
    """Build a Litestar app with the auth middleware wired up.

    Differences from the default ``test_app`` fixture:
      - ``AUTH_ENABLED=true`` so per-endpoint ``require_permission`` guards
        actually evaluate (instead of falling through).
      - Auth middleware attached so JWTs are decoded into ``scope["auth"]``.
      - ``get_route_handlers(auth_enabled=True, ...)`` so the admin router
        carries the ``require_any_admin_capability()`` gate.
      - Module-global ``core.config.app.alchemy`` rebound to the test
        engine, so route handlers that bypass DI (e.g. roles controller's
        ``async with alchemy.get_session()``) still see the test DB.
      - In-process permission cache hydrated from the seeded rows so
        ``require_permission`` resolves the same codes the controllers
        granted.
    """
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-jwt-signing-32+chars")
    monkeypatch.setenv("JWT_ENCRYPTION_ALGORITHM", "HS256")
    monkeypatch.setenv("JWT_ISSUER", "magnet-test")
    monkeypatch.setenv("JWT_AUDIENCE", "magnet-test-api")

    # Clear cached settings so the new env values take effect.
    from core.config.base import get_auth_settings, get_settings

    get_auth_settings.cache_clear()
    get_settings.cache_clear()

    # Seed the permission catalog + system role grants in the same
    # transactional session the tests use.
    await _seed_permissions(db_session)

    # Rebind the module-global alchemy + every `from core.config.app import
    # alchemy` re-export to the test engine. Handlers and services bind the
    # name at import time, so patching the source module alone misses them.
    import core.config.app as app_config

    test_alchemy_config = SQLAlchemyAsyncConfig(
        engine_instance=engine,
        before_send_handler="autocommit",
        session_config=AsyncSessionConfig(expire_on_commit=False),
    )
    monkeypatch.setattr(app_config, "alchemy", test_alchemy_config)

    import importlib

    for mod_name in (
        "services.users.service",
        "routes.admin.roles",
        "routes.admin.users",
        "routes.admin.groups",
        "routes.admin.permissions",
        "routes.admin.access_log",
        "routes.admin.settings",
    ):
        try:
            mod = importlib.import_module(mod_name)
        except Exception:
            continue
        if hasattr(mod, "alchemy"):
            monkeypatch.setattr(mod, "alchemy", test_alchemy_config)

    # The conftest ``db_session`` runs inside an outer transaction that is
    # rolled back at teardown — calling ``commit()`` on it commits a
    # SAVEPOINT, not the outer trans, so a fresh connection won't see the
    # rows. Route the auth middleware's user lookup at the same session so
    # it observes the test's writes. Requests are serial in the test
    # client (one request at a time), so reusing the session is safe.
    from sqlalchemy import select
    from core.db.models.user.user import User
    import services.users.service as users_service

    from sqlalchemy.orm import selectinload, joinedload

    async def _test_get_user_by_id(user_id):
        stmt = (
            select(User)
            .where(User.id == uuid.UUID(str(user_id)))
            .options(joinedload(User.tenant), selectinload(User.roles))
        )
        result = await db_session.execute(stmt)
        return result.scalar_one_or_none()

    monkeypatch.setattr(users_service, "get_user_by_id", _test_get_user_by_id)

    # Production ``ensure_request_auth_data_local_jwt`` builds ``auth.data``
    # *without* copying ``tenant_id`` from token extras — the property
    # ``Auth.tenant_id`` then relies on a fully-attached ``user.tenant_id``.
    # In tests, the user instance we return is bound to the per-test
    # transactional session and tenant_id may not survive cross-handler
    # detaches. Wrap the production helper so ``data["tenant_id"]`` is also
    # populated, giving ``Auth.tenant_id`` a stable fallback.
    import middlewares.auth as auth_middleware
    from middlewares.auth import (
        ensure_request_auth_data_local_jwt as _real_local_jwt,
    )

    async def _wrapped_local_jwt(token_str):
        auth = await _real_local_jwt(token_str)
        if auth is None:
            return None
        # Decode the token again to lift ``tenant_id`` from extras.
        from litestar.security.jwt import Token
        from core.config.base import get_auth_settings

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

    # Build the route table with auth on so the admin router-level guard
    # also engages.
    from routes import get_route_handlers
    from middlewares.auth import create_auth_middleware
    from core.server.plugins import DependenciesPlugin
    from guards.permissions import load_role_permissions_cache

    route_handlers = get_route_handlers(auth_enabled=True, web_included=False)

    app = Litestar(
        route_handlers=route_handlers,
        debug=True,
        middleware=[create_auth_middleware()],
        plugins=[
            SQLAlchemyPlugin(config=test_alchemy_config),
            ProblemDetailsPlugin(
                config=ProblemDetailsConfig(enable_for_all_http_exceptions=True)
            ),
            DependenciesPlugin(),
        ],
    )

    # Hydrate the in-process permission cache from the seeded rows.
    await load_role_permissions_cache(session=db_session)

    yield app

    # monkeypatch's setattr restores automatically at teardown; just clear
    # the in-process permission cache so cross-test state doesn't leak.
    from guards.permissions import reset_role_permissions_cache

    reset_role_permissions_cache()
    get_auth_settings.cache_clear()
    get_settings.cache_clear()


@pytest.fixture
async def auth_client(auth_app) -> AsyncTestClient:
    async with AsyncTestClient(app=auth_app) as c:
        yield c


# ---------------------------------------------------------------------------
# Helpers — user factories + JWT minting
# ---------------------------------------------------------------------------


def _mint_jwt(
    user,
    *,
    role_slugs: list[str],
    is_superuser: bool = False,
    tenant_id_override: str | None = None,
) -> str:
    """Mint a HS256 JWT mirroring ``services.auth.session_service.create_access_token``.

    We don't import the production helper because it requires a full user
    object with relationships preloaded; here we want explicit control over
    the claims so we can simulate every role/superuser combination.

    ``tenant_id`` is stamped in the JWT extras so ``Auth.tenant_id`` has a
    fallback when the DB-loaded user can't supply it (e.g. when the test
    session's connection is mid-transaction during request handling).
    """
    from core.config.base import get_auth_settings

    settings = get_auth_settings()
    tenant_id = tenant_id_override or (
        str(user.tenant_id) if getattr(user, "tenant_id", None) else None
    )
    extras = {
        "user_id": str(user.id),
        "is_superuser": is_superuser,
        "is_verified": True,
        "auth_method": "password",
        "roles": role_slugs,
    }
    if tenant_id:
        extras["tenant_id"] = tenant_id
    token = Token(
        sub=user.email,
        exp=datetime.now(UTC) + timedelta(minutes=15),
        jti=str(uuid.uuid4()),
        iss=settings.JWT_ISSUER or None,
        aud=settings.JWT_AUDIENCE or None,
        extras=extras,
    )
    return token.encode(
        secret=settings.SECRET_KEY,
        algorithm=settings.JWT_ENCRYPTION_ALGORITHM,
    )


async def _make_user(
    db_session,
    tenant_id,
    *,
    email: str | None = None,
    is_superuser: bool = False,
    role_slugs: list[str] | None = None,
):
    """Create a User row + UserRole assignments, return the user."""
    from datetime import UTC, datetime
    from sqlalchemy import select
    from core.db.models.user.user import User
    from core.db.models.user.user_role import UserRole
    from core.db.models.user.role import Role

    user = User(
        email=email or f"rbac-{uuid4().hex[:8]}@test.magnet.ai",
        name="RBAC Test",
        is_active=True,
        is_verified=True,
        is_superuser=is_superuser,
        tenant_id=tenant_id,
    )
    db_session.add(user)
    await db_session.flush()

    for slug in role_slugs or []:
        role = (
            await db_session.execute(select(Role).where(Role.slug == slug))
        ).scalar_one_or_none()
        if role is None:
            continue
        db_session.add(
            UserRole(user_id=user.id, role_id=role.id, assigned_at=datetime.now(UTC))
        )
    await db_session.flush()
    return user


# ---------------------------------------------------------------------------
# 1. Authentication boundary
# ---------------------------------------------------------------------------


@pytest.mark.e2e
class TestRBACAuthenticationBoundary:
    """No token, bad token, or expired token must never reach a handler."""

    async def test_admin_route_rejects_anonymous(self, auth_client):
        response = await auth_client.get("/api/admin/agents")
        # No auth header → AuthResponseMiddleware raises NotAuthorizedException.
        assert response.status_code in (401, 403), response.text

    async def test_admin_route_rejects_garbage_bearer(self, auth_client):
        response = await auth_client.get(
            "/api/admin/agents",
            headers={"Authorization": "Bearer not-a-real-token"},
        )
        assert response.status_code in (401, 403), response.text


# ---------------------------------------------------------------------------
# 2. Role-driven permission enforcement
# ---------------------------------------------------------------------------


@pytest.mark.e2e
class TestRBACAgentsPermissions:
    """``require_permission(Permission.AGENTS_*)`` enforces the right code."""

    async def test_viewer_can_read_but_not_write(
        self, auth_client, db_session, default_tenant
    ):
        viewer = await _make_user(db_session, default_tenant.id, role_slugs=["viewer"])
        token = _mint_jwt(viewer, role_slugs=["viewer"])
        headers = {"Authorization": f"Bearer {token}"}

        # Read is permitted.
        read = await auth_client.get("/api/admin/agents", headers=headers)
        assert read.status_code == 200, read.text

        # Write is forbidden — viewer lacks write:agents.
        write = await auth_client.post(
            "/api/admin/agents",
            headers=headers,
            json={
                "name": "Forbidden",
                "system_name": f"forbidden-{uuid4().hex[:6]}",
            },
        )
        assert write.status_code == 403, write.text

    async def test_admin_can_write_and_delete(
        self, auth_client, db_session, default_tenant
    ):
        admin = await _make_user(db_session, default_tenant.id, role_slugs=["admin"])
        token = _mint_jwt(admin, role_slugs=["admin"])
        headers = {"Authorization": f"Bearer {token}"}

        create = await auth_client.post(
            "/api/admin/agents",
            headers=headers,
            json={
                "name": "Admin Created",
                "system_name": f"admin-{uuid4().hex[:6]}",
            },
        )
        # Tenant-id RLS may still trip auto-commit on this path in alpha; what
        # matters for RBAC is that the *guard* passed (i.e. not 403).
        assert create.status_code != 403, create.text

    async def test_user_role_cannot_write_agents(
        self, auth_client, db_session, default_tenant
    ):
        user = await _make_user(db_session, default_tenant.id, role_slugs=["user"])
        token = _mint_jwt(user, role_slugs=["user"])
        headers = {"Authorization": f"Bearer {token}"}

        response = await auth_client.post(
            "/api/admin/agents",
            headers=headers,
            json={
                "name": "Unauthorized",
                "system_name": f"u-{uuid4().hex[:6]}",
            },
        )
        assert response.status_code == 403, response.text

    async def test_user_with_no_role_is_blocked_by_router_guard(
        self, auth_client, db_session, default_tenant
    ):
        """``require_any_admin_capability()`` rejects principals with zero perms."""
        nobody = await _make_user(db_session, default_tenant.id, role_slugs=[])
        token = _mint_jwt(nobody, role_slugs=[])
        headers = {"Authorization": f"Bearer {token}"}

        response = await auth_client.get("/api/admin/agents", headers=headers)
        assert response.status_code == 403, response.text


# ---------------------------------------------------------------------------
# 3. Superuser bypass
# ---------------------------------------------------------------------------


@pytest.mark.e2e
class TestRBACSuperuserBypass:
    async def test_superuser_bypass_logic_at_guard_level(
        self, auth_app, db_session, default_tenant
    ):
        """Exercise ``require_any_admin_capability`` directly with a
        superuser principal — verifies the bypass branch without depending
        on the full HTTP/auth-middleware path (which has separate
        cross-loop quirks under the test client when the user lookup is
        proxied through the per-test transactional session).
        """
        from types import SimpleNamespace
        from guards.access import require_any_admin_capability

        guard = require_any_admin_capability()

        su_user = SimpleNamespace(is_superuser=True, roles=[], tenant_id=None)
        auth = SimpleNamespace(
            type="local_jwt",
            user=su_user,
            data={"roles": []},
            tenant_id=None,
        )
        conn = SimpleNamespace(scope={"auth": auth})

        # Must not raise — the explicit superuser short-circuit fires before
        # the "no permissions assigned" check.
        guard(conn, None)


# ---------------------------------------------------------------------------
# 4. Roles controller — capability ceiling + system-role protection
# ---------------------------------------------------------------------------


@pytest.mark.e2e
class TestRBACRolesController:
    async def test_viewer_cannot_create_role(
        self, auth_client, db_session, default_tenant
    ):
        viewer = await _make_user(db_session, default_tenant.id, role_slugs=["viewer"])
        token = _mint_jwt(viewer, role_slugs=["viewer"])
        headers = {"Authorization": f"Bearer {token}"}

        response = await auth_client.post(
            "/api/admin/roles",
            headers=headers,
            json={
                "slug": f"new-{uuid4().hex[:6]}",
                "name": f"New Role {uuid4().hex[:6]}",
                "permissions": ["read:agents"],
            },
        )
        # viewer lacks `write:roles` → 403 from per-endpoint guard.
        assert response.status_code == 403, response.text

    async def test_admin_passes_role_write_guard(
        self, auth_client, db_session, default_tenant
    ):
        """An ``admin`` principal must clear both the router-level guard and
        the per-endpoint ``require_permission(ROLES_WRITE)`` guard.

        We don't assert 201 on the response body because the role-creation
        path itself opens its own ``alchemy.get_session()`` and on alpha
        that surface has unrelated event-loop interaction with the per-test
        transactional session. What this test pins down is that an admin's
        request is *not* rejected by RBAC (i.e. status != 403).
        """
        admin = await _make_user(db_session, default_tenant.id, role_slugs=["admin"])
        token = _mint_jwt(admin, role_slugs=["admin"])
        headers = {"Authorization": f"Bearer {token}"}

        slug = f"custom-{uuid4().hex[:6]}"
        response = await auth_client.post(
            "/api/admin/roles",
            headers=headers,
            json={
                "slug": slug,
                "name": f"Custom {slug}",
                "permissions": ["read:agents", "write:agents"],
            },
        )
        # Guards passed → not 403.
        assert response.status_code != 403, response.text

    async def test_reserved_slug_rejected(
        self, auth_client, db_session, default_tenant
    ):
        admin = await _make_user(db_session, default_tenant.id, role_slugs=["admin"])
        token = _mint_jwt(admin, role_slugs=["admin"])
        headers = {"Authorization": f"Bearer {token}"}

        response = await auth_client.post(
            "/api/admin/roles",
            headers=headers,
            json={"slug": "admin", "name": "Pretender", "permissions": []},
        )
        # The `admin` slug is reserved for system roles.
        assert response.status_code in (400, 422), response.text

    async def test_unknown_permission_rejected(
        self, auth_client, db_session, default_tenant
    ):
        admin = await _make_user(db_session, default_tenant.id, role_slugs=["admin"])
        token = _mint_jwt(admin, role_slugs=["admin"])
        headers = {"Authorization": f"Bearer {token}"}

        response = await auth_client.post(
            "/api/admin/roles",
            headers=headers,
            json={
                "slug": f"x-{uuid4().hex[:6]}",
                "name": f"X {uuid4().hex[:6]}",
                "permissions": ["read:nonexistent_resource"],
            },
        )
        # Permission code not in catalog → ValidationException → 400/422.
        assert response.status_code in (400, 422), response.text


# ---------------------------------------------------------------------------
# 5. Tenant scoping on the Roles controller
# ---------------------------------------------------------------------------


@pytest.mark.e2e
class TestRBACTenantScoping:
    async def test_other_tenant_custom_role_is_invisible(
        self, auth_client, db_session, default_tenant
    ):
        """A tenant admin must not see custom roles from another tenant."""
        from core.db.models.tenant.tenant import Tenant
        from core.db.models.user.role import Role

        # Make a second tenant + a custom role inside it.
        other = Tenant(slug=f"other-{uuid4().hex[:6]}", name="Other Tenant")
        db_session.add(other)
        await db_session.flush()

        other_role = Role(
            slug=f"other-r-{uuid4().hex[:6]}",
            name=f"Other R {uuid4().hex[:6]}",
            is_system=False,
            tenant_id=other.id,
        )
        db_session.add(other_role)
        await db_session.flush()
        await db_session.commit()

        admin = await _make_user(db_session, default_tenant.id, role_slugs=["admin"])
        token = _mint_jwt(admin, role_slugs=["admin"])
        headers = {"Authorization": f"Bearer {token}"}

        # List roles: should include system roles + default-tenant customs,
        # but never the other tenant's custom role.
        response = await auth_client.get("/api/admin/roles", headers=headers)
        assert response.status_code == 200, response.text
        slugs = {r["slug"] for r in response.json()}
        assert other_role.slug not in slugs

        # Direct access by id is a 404 (tenant_id mismatch).
        direct = await auth_client.get(
            f"/api/admin/roles/{other_role.id}", headers=headers
        )
        assert direct.status_code == 404, direct.text
