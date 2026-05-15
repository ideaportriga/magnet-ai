"""Unit tests for `services.access_control.record_level` helpers.

These are pure-Python tests: no DB session, no Litestar app. The helpers are
the per-resource controller glue (PR 10) — they need to behave predictably
under unauthenticated, authenticated, and superuser auth shapes.

Integration coverage of the full pipeline (auth → PermissionService → 404
vs 403 vs 200) lives in `tests/integration/domain/test_record_level_access.py`
and `test_pr10_rollout_coverage.py`. These unit tests guard the small
boilerplate around them so a regression here is caught without spinning up
the whole stack.
"""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest


# `services.access_control` pulls `core.db.models.access_grant`, which
# triggers `core.db.models.__init__`. Without the `engine` fixture (which
# unit tests don't request), that init runs in an order that re-enters
# `core.domain.providers.controller` mid-import → circular ImportError.
#
# The fix: pre-load the whole models package by walking the same path the
# integration conftest does. After this, individual submodule imports
# resolve to the cached package state and the cycle never re-enters.
def _warmup_models() -> None:
    # Pre-warm the same load order the integration conftest uses (see
    # `_import_all_models` in `tests/conftest.py`). Without this, importing
    # `services.access_control` from a unit test re-enters the
    # controller↔model package init cycle and fails.
    try:
        from core.config.base import get_general_settings  # noqa: F401
        import core.db.rls_context  # noqa: F401
        import core.db.models  # noqa: F401
    except ImportError:
        pass


_warmup_models()


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


def _make_request(auth=None):
    """Build a minimal object that behaves like `litestar.Request` for
    `request.scope.get("auth")`."""
    scope = {"auth": auth}
    return SimpleNamespace(scope=scope)


def _make_auth(*, tenant_id=None, user_id=None, is_superuser=False):
    """Auth shape used by the access_control helpers — exposes `tenant_id`
    and `user` (with `.id`, `.is_superuser`)."""
    user = (
        SimpleNamespace(id=user_id, is_superuser=is_superuser, roles=[])
        if user_id is not None or is_superuser
        else None
    )
    return SimpleNamespace(tenant_id=tenant_id, user=user)


# ---------------------------------------------------------------------------
# force_create_fields — payload sanitization
# ---------------------------------------------------------------------------


class TestForceCreateFields:
    def test_stamps_tenant_and_owner_from_auth(self):
        from services.access_control import force_create_fields

        tenant_id = str(uuid4())
        user_id = str(uuid4())
        request = _make_request(_make_auth(tenant_id=tenant_id, user_id=user_id))

        payload = force_create_fields({"name": "X"}, request=request)

        assert payload["tenant_id"] == tenant_id
        assert payload["owner_id"] == user_id

    def test_overwrites_client_supplied_tenant_id(self):
        """Auth context is the source of truth; client payloads can lie."""
        from services.access_control import force_create_fields

        auth_tenant = str(uuid4())
        spoof_tenant = str(uuid4())
        request = _make_request(_make_auth(tenant_id=auth_tenant, user_id=str(uuid4())))

        payload = force_create_fields(
            {"name": "X", "tenant_id": spoof_tenant}, request=request
        )

        assert payload["tenant_id"] == auth_tenant
        assert payload["tenant_id"] != spoof_tenant

    def test_strips_client_supplied_audit_fields(self):
        """`created_by` / `updated_by` come from the audit_username dep,
        never from the request body."""
        from services.access_control import force_create_fields

        request = _make_request(
            _make_auth(tenant_id=str(uuid4()), user_id=str(uuid4()))
        )

        payload = force_create_fields(
            {
                "name": "X",
                "created_by": "evil@example.com",
                "updated_by": "evil@example.com",
            },
            request=request,
        )

        assert "created_by" not in payload
        assert "updated_by" not in payload

    def test_noop_when_auth_absent(self):
        """In test-mode / unauthenticated calls the payload is unchanged."""
        from services.access_control import force_create_fields

        request = _make_request(auth=None)
        payload = force_create_fields({"name": "X"}, request=request)
        assert payload == {"name": "X"}

    def test_no_owner_id_when_user_missing(self):
        """An auth without a `.user` (e.g. API key auth without principal)
        still stamps tenant_id but cannot stamp owner_id."""
        from services.access_control import force_create_fields

        tenant_id = str(uuid4())
        request = _make_request(_make_auth(tenant_id=tenant_id, user_id=None))
        payload = force_create_fields({"name": "X"}, request=request)
        assert payload["tenant_id"] == tenant_id
        assert "owner_id" not in payload


# ---------------------------------------------------------------------------
# enforce_view_or_404 / enforce_action_or_403 — auth-off no-ops
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestEnforceAuthOff:
    """When auth middleware isn't on the request (test mode / dev server with
    auth disabled), the enforcers must be pure no-ops — they cannot block the
    request. Backend security still applies via the route guards."""

    async def test_enforce_view_or_404_noop(self):
        from services.access_control import enforce_view_or_404

        # No auth in scope → returns None without touching service.
        await enforce_view_or_404(
            service=SimpleNamespace(),  # unused
            request=_make_request(auth=None),
            resource=SimpleNamespace(),
            resource_type="agents",
        )

    async def test_enforce_action_or_403_noop(self):
        from services.access_control import enforce_action_or_403

        await enforce_action_or_403(
            service=SimpleNamespace(),
            request=_make_request(auth=None),
            action="edit",
            resource=SimpleNamespace(),
            resource_type="agents",
        )


# ---------------------------------------------------------------------------
# attach_permissions — schema decoration
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestAttachPermissions:
    async def test_noop_when_auth_absent(self):
        from services.access_control import attach_permissions

        schema = SimpleNamespace(permissions=None)
        result = await attach_permissions(
            service=SimpleNamespace(),
            schema=schema,
            obj=SimpleNamespace(),
            request=_make_request(auth=None),
            resource_type="agents",
        )
        # Same object returned; permissions untouched.
        assert result is schema
        assert schema.permissions is None

    async def test_noop_when_schema_has_no_permissions_field(self):
        """Schemas that haven't adopted the `RecordLevelFieldsMixin` don't
        carry a `permissions` field; the helper must skip them safely."""
        from services.access_control import attach_permissions

        schema = SimpleNamespace()  # no `permissions` attribute
        result = await attach_permissions(
            service=SimpleNamespace(),
            schema=schema,
            obj=SimpleNamespace(),
            request=_make_request(_make_auth(tenant_id=str(uuid4()))),
            resource_type="agents",
        )
        assert result is schema
        assert not hasattr(schema, "permissions")


# ---------------------------------------------------------------------------
# visibility_filter_for — auth-off returns None (caller skips filtering)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestVisibilityFilterFor:
    async def test_returns_none_when_auth_absent(self):
        """Test-mode / auth-off: the helper signals 'no filter' so the
        endpoint returns everything visible under RLS."""
        from services.access_control import visibility_filter_for

        result = await visibility_filter_for(
            service=SimpleNamespace(),
            request=_make_request(auth=None),
            model=SimpleNamespace(),
            resource_type="agents",
        )
        assert result is None
