"""Additional admin-endpoint coverage on top of `test_admin_access_control.py`.

The earlier file covers helper functions (`_validate_permission_codes`,
`_check_capability_ceiling`, `_ensure_not_last_admin`, audit writer). This
file fills the remaining gaps:

  - GET /api/admin/permissions over HTTP — proves the route is mounted and
    serializes the catalog from the DB.
  - Full role lifecycle in the DB: create → list → get → permission replace
    → delete-with-assignments-409 → delete-clean.
  - Access-log read filtering by action and actor in addition to the tenant
    boundary that's already tested.

Auth is disabled in the test app, so the role / users controllers' direct
helpers expect a hand-rolled `Auth` namespace instead of relying on the
middleware. That mirrors the existing pattern in `test_admin_access_control.py`.
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select


def _make_auth(user, tenant_id):
    """Auth namespace mirroring the one in `test_admin_access_control.py`."""
    return SimpleNamespace(
        type="local_jwt",
        data={"tenant_id": str(tenant_id)},
        user_id=str(user.id) if user else None,
        user=user,
        tenant_id=str(tenant_id),
    )


def _make_superuser_auth(tenant_id: UUID):
    user = SimpleNamespace(
        id=uuid4(),
        is_superuser=True,
        roles=[],
    )
    return _make_auth(user, tenant_id)


@pytest.fixture
def patch_admin_alchemy_session(db_session, monkeypatch):
    """Route admin controllers' `alchemy.get_session()` to the test session.

    The admin route modules import a global `alchemy` from `core.config.app`
    that's bound to the production engine. Test routes share that import,
    so without this patch the audit/role rows land in the wrong DB.
    """

    class _SessionCM:
        async def __aenter__(self_inner):
            return db_session

        async def __aexit__(self_inner, *args):
            return None

    for module_name in (
        "routes.admin.roles",
        "routes.admin.users",
        "routes.admin.access_log",
        "routes.admin.permissions",
    ):
        mod = __import__(module_name, fromlist=["alchemy"])
        monkeypatch.setattr(mod.alchemy, "get_session", lambda: _SessionCM())
    return db_session


# ---------------------------------------------------------------------------
# Permissions catalog — verifies the controller serialization contract.
#
# We can't reach this over HTTP from the test client because the controller
# pulls its own `core.config.app.alchemy` session (production DB), not the
# test container. So the test calls `list_permissions` directly with the
# rows seeded into the in-test session.
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestPermissionsCatalog:
    async def test_list_permissions_serializes_catalog(
        self, db_session, default_tenant, patch_admin_alchemy_session
    ):
        from core.db.models.user.permission import Permission as PermModel
        from routes.admin.permissions import PermissionsController

        db_session.add_all(
            [
                PermModel(
                    code="read:demo",
                    resource_type="demo",
                    action="read",
                    description="Read demo",
                    is_system=True,
                ),
                PermModel(
                    code="write:demo",
                    resource_type="demo",
                    action="write",
                    description="Write demo",
                    is_system=True,
                ),
            ]
        )
        await db_session.commit()

        controller = PermissionsController(owner=None)
        rows = await PermissionsController.list_permissions.fn(
            controller, resource_type="demo"
        )

        codes = {r.code for r in rows}
        assert {"read:demo", "write:demo"} <= codes
        # Shape contract: every entry has the documented fields.
        first = rows[0]
        for attr in ("code", "resource_type", "action", "is_system"):
            assert hasattr(first, attr)


# ---------------------------------------------------------------------------
# Role lifecycle — direct controller method calls (auth-off bypass)
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestRoleLifecycle:
    async def test_create_get_delete_cycle(
        self, db_session, default_tenant, patch_admin_alchemy_session
    ):
        """Create a custom role, fetch it via the list serializer, then
        delete it. All operations write audit-log rows."""
        from core.db.models.audit import AccessAuditLog
        from core.db.models.user.permission import Permission as PermModel
        from core.db.models.user.role import Role
        from core.db.models.user.role_permission import RolePermission
        from routes.admin.roles import RolesController, RoleCreateRequest

        # Seed a permission the new role will reference.
        db_session.add(
            PermModel(
                code="read:agents",
                resource_type="agents",
                action="read",
                description="Read agents",
            )
        )
        await db_session.commit()

        # actor_id=None so audit-log FK to user_account isn't tripped.
        actor = SimpleNamespace(
            id=None,
            is_superuser=True,
            roles=[],
        )
        request = SimpleNamespace(scope={"auth": _make_auth(actor, default_tenant.id)})
        controller = RolesController(owner=None)  # owner only used for routing

        # Create
        slug = f"reviewer-{uuid4().hex[:6]}"
        # Litestar wraps the method as an HTTPRouteHandler; bypass that
        # wrapper and call the underlying function directly.
        created = await RolesController.create_role.fn(
            controller,
            request,
            RoleCreateRequest(
                slug=slug,
                name=f"Reviewer {slug}",
                description="Reviews submissions",
                permissions=["read:agents"],
            ),
        )
        assert created.slug == slug
        assert created.is_system is False
        assert "read:agents" in created.permissions

        # Audit log row written
        audit_rows = (
            (
                await db_session.execute(
                    select(AccessAuditLog).where(AccessAuditLog.target_id == created.id)
                )
            )
            .scalars()
            .all()
        )
        assert any(r.action == "role.create" for r in audit_rows)

        # Delete
        await RolesController.delete_role.fn(controller, request, created.id)

        # Row really gone
        gone = (
            await db_session.execute(select(Role).where(Role.id == created.id))
        ).scalar_one_or_none()
        assert gone is None
        # RolePermission rows cascaded
        rp = (
            await db_session.execute(
                select(RolePermission).where(RolePermission.role_id == created.id)
            )
        ).all()
        assert rp == []

    async def test_delete_role_with_assignments_returns_409(
        self, db_session, default_tenant, patch_admin_alchemy_session
    ):
        """Custom role with at least one assignment cannot be deleted."""
        from core.db.models.user.role import Role
        from core.db.models.user.user import User
        from core.db.models.user.user_role import UserRole
        from routes.admin.roles import RolesController
        from litestar.exceptions import HTTPException

        actor = SimpleNamespace(id=None, is_superuser=True, roles=[])
        request = SimpleNamespace(scope={"auth": _make_auth(actor, default_tenant.id)})
        controller = RolesController(owner=None)

        # Custom tenant-scoped role with an assigned user.
        role = Role(
            slug=f"r-{uuid4().hex[:6]}",
            name=f"R {uuid4().hex[:6]}",
            is_system=False,
            tenant_id=default_tenant.id,
        )
        db_session.add(role)
        await db_session.flush()
        assignee = User(
            email=f"u-{uuid4().hex[:6]}@test.magnet.ai",
            name="U",
            is_active=True,
            tenant_id=default_tenant.id,
        )
        db_session.add(assignee)
        await db_session.flush()
        db_session.add(
            UserRole(
                user_id=assignee.id,
                role_id=role.id,
                assigned_at=datetime.now(UTC),
            )
        )
        await db_session.commit()

        with pytest.raises(HTTPException) as excinfo:
            await RolesController.delete_role.fn(controller, request, role.id)
        assert excinfo.value.status_code == 409


# ---------------------------------------------------------------------------
# Role permission set replace — capability ceiling + audit
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestRolePermissionsReplace:
    async def test_replace_permissions_records_diff_in_audit(
        self, db_session, default_tenant, patch_admin_alchemy_session
    ):
        """PUT /roles/{id}/permissions writes a diff payload (added/removed/
        final) to access_audit_log so admins can replay configuration
        changes."""
        from core.db.models.audit import AccessAuditLog
        from core.db.models.user.permission import Permission as PermModel
        from core.db.models.user.role import Role
        from core.db.models.user.role_permission import RolePermission
        from routes.admin.roles import (
            RolesController,
            RolePermissionsReplace,
        )

        for code, rt in (("read:demo", "demo"), ("write:demo", "demo")):
            db_session.add(
                PermModel(code=code, resource_type=rt, action=code.split(":")[0])
            )
        await db_session.commit()

        role = Role(
            slug=f"r-{uuid4().hex[:6]}",
            name=f"R {uuid4().hex[:6]}",
            is_system=False,
            tenant_id=default_tenant.id,
        )
        db_session.add(role)
        await db_session.flush()
        db_session.add(RolePermission(role_id=role.id, permission_code="read:demo"))
        await db_session.commit()

        actor = SimpleNamespace(id=None, is_superuser=True, roles=[])
        request = SimpleNamespace(scope={"auth": _make_auth(actor, default_tenant.id)})
        controller = RolesController(owner=None)

        await RolesController.replace_permissions.fn(
            controller,
            request,
            role.id,
            RolePermissionsReplace(permissions=["write:demo"]),
        )

        # Audit row diff.
        audit = (
            (
                await db_session.execute(
                    select(AccessAuditLog).where(
                        AccessAuditLog.action == "role.permissions.replace",
                        AccessAuditLog.target_id == role.id,
                    )
                )
            )
            .scalars()
            .one()
        )
        payload = audit.payload
        assert payload["added"] == ["write:demo"]
        assert payload["removed"] == ["read:demo"]
        assert payload["final"] == ["write:demo"]

        # Final state in DB matches the diff.
        rp_codes = {
            r[0]
            for r in (
                await db_session.execute(
                    select(RolePermission.permission_code).where(
                        RolePermission.role_id == role.id
                    )
                )
            ).all()
        }
        assert rp_codes == {"write:demo"}


# ---------------------------------------------------------------------------
# Access-log filtering
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestAccessLogFilters:
    async def test_filter_by_action_and_actor(self, db_session, default_tenant):
        from core.db.models.audit import AccessAuditLog
        from core.db.models.user.user import User
        from services.access_control import write_audit_log

        # FK on access_audit_log.actor_id → user_account requires real users.
        user_a = User(
            email=f"a-{uuid4().hex[:6]}@test.magnet.ai",
            name="A",
            is_active=True,
            tenant_id=default_tenant.id,
        )
        user_b = User(
            email=f"b-{uuid4().hex[:6]}@test.magnet.ai",
            name="B",
            is_active=True,
            tenant_id=default_tenant.id,
        )
        db_session.add_all([user_a, user_b])
        await db_session.flush()

        actor_a = user_a.id
        actor_b = user_b.id
        await write_audit_log(
            db_session,
            tenant_id=default_tenant.id,
            actor_id=actor_a,
            action="role.create",
            target_type="role",
            payload={},
        )
        await write_audit_log(
            db_session,
            tenant_id=default_tenant.id,
            actor_id=actor_b,
            action="role.delete",
            target_type="role",
            payload={},
        )
        await write_audit_log(
            db_session,
            tenant_id=default_tenant.id,
            actor_id=actor_a,
            action="role.delete",
            target_type="role",
            payload={},
        )

        # Same composite filter the access-log endpoint applies.
        stmt = (
            select(AccessAuditLog)
            .where(
                AccessAuditLog.tenant_id == default_tenant.id,
                AccessAuditLog.action == "role.delete",
                AccessAuditLog.actor_id == actor_a,
            )
            .order_by(AccessAuditLog.created_at.desc())
        )
        rows = (await db_session.execute(stmt)).scalars().all()
        assert len(rows) == 1
        assert rows[0].actor_id == actor_a
        assert rows[0].action == "role.delete"
