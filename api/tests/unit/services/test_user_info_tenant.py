"""Unit tests for `build_user_info` tenant block + `Auth.tenant_id` property.

Pure-Python: no DB. The User/Tenant/Auth dataclasses are stubbed to focus on
the contract introduced in PR 4 of the access-control plan.
"""

from __future__ import annotations

# Warm the import graph before `services.auth.user_info` is loaded, which
# transitively pulls in the (pre-existing) provider ↔ services circular chain.
import core.config.app  # noqa: F401

import asyncio
from types import SimpleNamespace
from uuid import uuid4

import pytest


def _make_user(tenant=None, roles=None, **kw):
    user = SimpleNamespace(
        id=uuid4(),
        email="u@example.com",
        name="U",
        avatar_url=None,
        is_verified=True,
        is_superuser=False,
        is_two_factor_enabled=False,
        last_login_at=None,
        tenant=tenant,
        roles=roles or [],
    )
    for k, v in kw.items():
        setattr(user, k, v)
    return user


def _make_tenant(slug="default", name="Default"):
    return SimpleNamespace(id=uuid4(), slug=slug, name=name)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@pytest.fixture(autouse=True)
def _no_related_load(monkeypatch):
    """Short-circuit the /me related-info loader (DB-free)."""
    import services.auth.user_info as mod

    async def _empty(_user):
        return [], [], []

    monkeypatch.setattr(mod, "_load_related_user_info", _empty)


def test_me_returns_tenant_block_when_user_has_tenant():
    from middlewares.auth import Auth
    from services.auth.user_info import build_user_info

    tenant = _make_tenant(slug="acme", name="Acme Inc.")
    user = _make_user(tenant=tenant)
    auth = Auth(type="local_jwt", data={}, user_id=str(user.id), user=user)

    info = asyncio.get_event_loop().run_until_complete(build_user_info(user, auth))
    assert info["tenant"] == {
        "id": str(tenant.id),
        "slug": "acme",
        "name": "Acme Inc.",
    }


def test_me_tenant_block_is_none_when_user_has_no_tenant():
    from middlewares.auth import Auth
    from services.auth.user_info import build_user_info

    user = _make_user(tenant=None)
    auth = Auth(type="local_jwt", data={}, user_id=str(user.id), user=user)

    info = asyncio.get_event_loop().run_until_complete(build_user_info(user, auth))
    assert info["tenant"] is None


def test_me_includes_role_is_system_flag():
    """Roles in the detailed block carry the DB-backed is_system value."""
    from middlewares.auth import Auth
    from services.auth.user_info import build_user_info

    tenant = _make_tenant()
    admin_role = SimpleNamespace(id=uuid4(), slug="admin", name="Admin", is_system=True)
    custom_role = SimpleNamespace(
        id=uuid4(), slug="reviewer", name="Reviewer", is_system=False
    )
    user = _make_user(tenant=tenant, roles=[admin_role, custom_role])
    auth = Auth(type="local_jwt", data={}, user_id=str(user.id), user=user)

    info = asyncio.get_event_loop().run_until_complete(build_user_info(user, auth))
    by_slug = {r["slug"]: r for r in info["roles_detailed"]}
    assert by_slug["admin"]["is_system"] is True
    assert by_slug["reviewer"]["is_system"] is False


class TestAuthTenantIdProperty:
    def test_jwt_auth_reads_tenant_from_user(self):
        from middlewares.auth import Auth

        tenant = _make_tenant()
        user = _make_user(tenant=tenant)
        # The property reads from User.tenant_id, not from User.tenant.
        user.tenant_id = tenant.id
        auth = Auth(type="local_jwt", data={}, user_id=str(user.id), user=user)
        assert auth.tenant_id == str(tenant.id)

    def test_api_key_reads_tenant_from_data(self):
        from middlewares.auth import Auth

        tid = uuid4()
        auth = Auth(
            type="api_key",
            data={"tenant_id": str(tid), "scopes": ["read:agents"]},
            user_id="api_key:k",
        )
        assert auth.tenant_id == str(tid)

    def test_returns_none_when_no_tenant(self):
        from middlewares.auth import Auth

        auth = Auth(type="api_key", data={}, user_id="api_key:k")
        assert auth.tenant_id is None
