"""Unit tests for guards.permissions."""

from __future__ import annotations

import pytest

from guards.permissions import (
    Permission,
    SYSTEM_ROLE_DEFAULTS,
    get_effective_permissions,
    require_any_permission,
    require_permission,
)
from litestar.exceptions import PermissionDeniedException


class _FakeRole:
    def __init__(self, slug: str):
        self.slug = slug


class _FakeUser:
    def __init__(self, roles=None, is_superuser=False):
        self.roles = roles or []
        self.is_superuser = is_superuser


class _FakeAuth:
    def __init__(self, type_="local_jwt", data=None, user=None):
        self.type = type_
        self.data = data or {}
        self.user = user


class _FakeConn:
    def __init__(self, auth=None):
        self.scope = {"auth": auth} if auth is not None else {}


def test_admin_role_gets_all_permissions():
    auth = _FakeAuth(user=_FakeUser(roles=[_FakeRole("admin")]))
    perms = get_effective_permissions(auth)
    assert perms == {p.value for p in Permission}


def test_viewer_role_gets_only_read_permissions():
    auth = _FakeAuth(user=_FakeUser(roles=[_FakeRole("viewer")]))
    perms = get_effective_permissions(auth)
    assert perms == SYSTEM_ROLE_DEFAULTS["viewer"]
    assert all(p.startswith("read:") for p in perms)


def test_user_role_has_no_write_to_admin_resources():
    auth = _FakeAuth(user=_FakeUser(roles=[_FakeRole("user")]))
    perms = get_effective_permissions(auth)
    assert Permission.AGENTS_WRITE.value not in perms
    assert Permission.ROLES_WRITE.value not in perms
    assert Permission.AGENTS_READ.value in perms


def test_superuser_short_circuits_to_all_permissions():
    auth = _FakeAuth(user=_FakeUser(roles=[], is_superuser=True))
    perms = get_effective_permissions(auth)
    assert perms == {p.value for p in Permission}


def test_api_key_uses_scopes_as_ceiling_without_role_union():
    auth = _FakeAuth(
        type_="api_key",
        data={"scopes": ["read:agents"], "roles": {"admin"}},
    )
    perms = get_effective_permissions(auth)
    # Role perms must NOT be unioned in for API keys.
    assert perms == {"read:agents"}


def test_api_key_without_scopes_fails_closed():
    auth = _FakeAuth(type_="api_key", data={})
    perms = get_effective_permissions(auth)
    assert perms == set()


def test_no_auth_returns_empty_set():
    assert get_effective_permissions(None) == set()


def test_require_permission_allows_when_held(monkeypatch):
    # Auth is enabled in this test → guard enforces.
    auth = _FakeAuth(user=_FakeUser(roles=[_FakeRole("admin")]))
    conn = _FakeConn(auth=auth)
    guard = require_permission(Permission.AGENTS_WRITE)
    guard(conn, None)  # should not raise


def test_require_permission_denies_when_missing():
    auth = _FakeAuth(user=_FakeUser(roles=[_FakeRole("viewer")]))
    conn = _FakeConn(auth=auth)
    guard = require_permission(Permission.AGENTS_WRITE)
    with pytest.raises(PermissionDeniedException):
        guard(conn, None)


def test_require_permission_requires_all_listed():
    auth = _FakeAuth(user=_FakeUser(roles=[_FakeRole("viewer")]))
    conn = _FakeConn(auth=auth)
    # viewer has read:agents but not write:agents → fails because we require BOTH
    guard = require_permission(Permission.AGENTS_READ, Permission.AGENTS_WRITE)
    with pytest.raises(PermissionDeniedException):
        guard(conn, None)


def test_require_any_permission_passes_with_one_match():
    auth = _FakeAuth(user=_FakeUser(roles=[_FakeRole("viewer")]))
    conn = _FakeConn(auth=auth)
    # viewer has read:agents → any-of passes
    guard = require_any_permission(Permission.AGENTS_READ, Permission.AGENTS_WRITE)
    guard(conn, None)


def test_require_permission_falls_through_when_auth_disabled(monkeypatch):
    from core.config import base as base_config

    # Simulate auth_enabled=False
    cached = base_config.get_auth_settings()
    monkeypatch.setattr(cached, "AUTH_ENABLED", False)

    conn = _FakeConn(auth=None)
    guard = require_permission(Permission.AGENTS_WRITE)
    guard(conn, None)  # should not raise


def test_require_permission_raises_when_auth_enabled_and_missing(monkeypatch):
    from core.config import base as base_config

    cached = base_config.get_auth_settings()
    monkeypatch.setattr(cached, "AUTH_ENABLED", True)

    conn = _FakeConn(auth=None)
    guard = require_permission(Permission.AGENTS_READ)
    with pytest.raises(PermissionDeniedException):
        guard(conn, None)


# ---------------------------------------------------------------------------
# DB-backed role → permission cache (PR 2)
# ---------------------------------------------------------------------------


def test_cache_wins_over_in_code_defaults(monkeypatch):
    """When the cache has a slug, it overrides SYSTEM_ROLE_DEFAULTS."""
    import guards.permissions as perms

    snapshot = {"user": frozenset({"read:agents", "write:agents"})}
    monkeypatch.setattr(perms, "_ROLE_PERMISSIONS_CACHE", snapshot)
    try:
        auth = _FakeAuth(user=_FakeUser(roles=[_FakeRole("user")]))
        effective = perms.get_effective_permissions(auth)
        assert effective == {"read:agents", "write:agents"}
        # Confirm we're NOT mixing in SYSTEM_ROLE_DEFAULTS['user']
        assert "execute:agents" not in effective
    finally:
        monkeypatch.setattr(perms, "_ROLE_PERMISSIONS_CACHE", None)


def test_loaded_cache_miss_fails_closed(monkeypatch):
    """After DB cache load, missing role grants do not resurrect defaults."""
    import guards.permissions as perms

    # Cache loaded but doesn't include `viewer`.
    snapshot = {"user": frozenset({"read:agents"})}
    monkeypatch.setattr(perms, "_ROLE_PERMISSIONS_CACHE", snapshot)
    try:
        auth = _FakeAuth(user=_FakeUser(roles=[_FakeRole("viewer")]))
        effective = perms.get_effective_permissions(auth)
        assert effective == set()
    finally:
        monkeypatch.setattr(perms, "_ROLE_PERMISSIONS_CACHE", None)


def test_reset_role_permissions_cache_clears_snapshot(monkeypatch):
    import guards.permissions as perms

    monkeypatch.setattr(perms, "_ROLE_PERMISSIONS_CACHE", {"x": frozenset({"y"})})
    perms.reset_role_permissions_cache()
    assert perms._ROLE_PERMISSIONS_CACHE is None


def test_custom_role_with_empty_grants_resolves_empty(monkeypatch):
    """Custom tenant role with no grants in cache → empty perms (no fallback)."""
    import guards.permissions as perms

    # Cache contains a custom role explicitly with empty grants.
    snapshot = {"custom-role": frozenset()}
    monkeypatch.setattr(perms, "_ROLE_PERMISSIONS_CACHE", snapshot)
    try:
        auth = _FakeAuth(user=_FakeUser(roles=[_FakeRole("custom-role")]))
        effective = perms.get_effective_permissions(auth)
        # Empty cache entry → empty perms (custom roles can't fall back to
        # system defaults because they're not in SYSTEM_ROLE_DEFAULTS either).
        assert effective == set()
    finally:
        monkeypatch.setattr(perms, "_ROLE_PERMISSIONS_CACHE", None)
