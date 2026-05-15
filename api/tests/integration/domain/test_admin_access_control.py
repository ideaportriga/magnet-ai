"""Integration tests for PR 5a admin access-control endpoints.

These exercise the SQL-level behaviour (validation queries, audit writes,
last-admin lockout) without booting the full Litestar app — the test fixture
runs with auth disabled, so the controller methods are invoked directly with
a mocked `Auth` and a real `db_session`.
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import select


def _make_auth(user, tenant_id):
    """Build an Auth-like object exposing `tenant_id` and `user`."""
    return SimpleNamespace(
        type="local_jwt",
        data={"tenant_id": str(tenant_id)},
        user_id=str(user.id) if user else None,
        user=user,
        tenant_id=str(tenant_id),
    )


@pytest.mark.integration
class TestAuditLogWriter:
    async def test_write_audit_log_roundtrip(self, db_session, default_tenant):
        from core.db.models.audit import AccessAuditLog
        from services.access_control import write_audit_log

        await write_audit_log(
            db_session,
            tenant_id=default_tenant.id,
            actor_id=None,
            action="role.create",
            target_type="role",
            target_id=uuid4(),
            payload={"slug": "reviewer", "permissions": ["read:agents"]},
        )

        rows = (
            (
                await db_session.execute(
                    select(AccessAuditLog).where(
                        AccessAuditLog.tenant_id == default_tenant.id
                    )
                )
            )
            .scalars()
            .all()
        )
        assert len(rows) == 1
        assert rows[0].action == "role.create"
        assert rows[0].payload["slug"] == "reviewer"


@pytest.mark.integration
class TestRolesControllerLogic:
    async def test_create_role_validates_permission_codes(
        self, db_session, default_tenant
    ):
        from routes.admin.roles import _validate_permission_codes

        # Seed one permission row so we can compare against unknowns.
        from core.db.models.user.permission import Permission as PermModel

        db_session.add(
            PermModel(
                code="read:agents",
                resource_type="agents",
                action="read",
            )
        )
        await db_session.flush()

        # Valid code → returns the set.
        valid = await _validate_permission_codes(db_session, ["read:agents"])
        assert valid == {"read:agents"}

        # Unknown code → ValidationException.
        from litestar.exceptions import ValidationException

        with pytest.raises(ValidationException):
            await _validate_permission_codes(db_session, ["write:nonexistent"])

    def test_capability_ceiling_blocks_unowned_permissions(self):
        from routes.admin.roles import _check_capability_ceiling
        from litestar.exceptions import PermissionDeniedException

        # Auth with no permissions cannot grant 'write:agents'.
        auth = SimpleNamespace(
            type="local_jwt",
            data={"roles": []},
            user=SimpleNamespace(is_superuser=False, roles=[]),
        )
        with pytest.raises(PermissionDeniedException):
            _check_capability_ceiling(auth, {"write:agents"})

    def test_capability_ceiling_allows_owned_permissions(self):
        from routes.admin.roles import _check_capability_ceiling

        admin_role = SimpleNamespace(slug="admin")
        auth = SimpleNamespace(
            type="local_jwt",
            data={},
            user=SimpleNamespace(is_superuser=False, roles=[admin_role]),
        )
        # Doesn't raise — admin role gets all permissions via fallback.
        _check_capability_ceiling(auth, {"read:agents", "write:agents"})

    def test_capability_ceiling_superuser_bypasses(self):
        from routes.admin.roles import _check_capability_ceiling

        auth = SimpleNamespace(
            type="local_jwt",
            data={},
            user=SimpleNamespace(is_superuser=True, roles=[]),
        )
        _check_capability_ceiling(auth, {"manage:resource_access"})


@pytest.mark.integration
class TestUsersControllerLogic:
    async def test_role_in_other_tenant_rejected(self, db_session, default_tenant):
        from core.db.models.tenant.tenant import Tenant
        from core.db.models.user.role import Role
        from routes.admin.users import _validate_roles_in_tenant
        from litestar.exceptions import ValidationException

        other = Tenant(slug=f"other-{uuid4().hex[:6]}", name="Other")
        db_session.add(other)
        await db_session.flush()

        other_role = Role(
            slug=f"r-{uuid4().hex[:6]}",
            name=f"R {uuid4().hex[:6]}",
            is_system=False,
            tenant_id=other.id,
        )
        db_session.add(other_role)
        await db_session.flush()

        with pytest.raises(ValidationException):
            _validate_roles_in_tenant({other_role.id: other_role}, default_tenant.id)

    async def test_system_role_passes_tenant_check(self, db_session, default_tenant):
        from core.db.models.user.role import Role
        from routes.admin.users import _validate_roles_in_tenant

        # Make a system-flavored role (tenant_id IS NULL).
        sys_role = Role(
            slug=f"sys-{uuid4().hex[:6]}",
            name=f"Sys {uuid4().hex[:6]}",
            is_system=True,
            tenant_id=None,
        )
        db_session.add(sys_role)
        await db_session.flush()

        # System roles are universally assignable → no exception.

        _validate_roles_in_tenant({sys_role.id: sys_role}, default_tenant.id)

    async def test_ensure_not_last_admin_blocks_when_solo(
        self, db_session, default_tenant
    ):
        from core.db.models.user.role import Role
        from core.db.models.user.user import User
        from core.db.models.user.user_role import UserRole
        from routes.admin.users import _ensure_not_last_admin
        from litestar.exceptions import HTTPException

        admin_role = Role(
            slug=f"adm-{uuid4().hex[:6]}",
            name=f"Adm {uuid4().hex[:6]}",
            is_system=True,
            tenant_id=None,
        )
        db_session.add(admin_role)
        await db_session.flush()

        solo_admin = User(
            email=f"solo-{uuid4().hex[:6]}@test.magnet.ai",
            name="Solo",
            is_active=True,
            tenant_id=default_tenant.id,
        )
        db_session.add(solo_admin)
        await db_session.flush()
        db_session.add(
            UserRole(
                user_id=solo_admin.id,
                role_id=admin_role.id,
                assigned_at=datetime.now(UTC),
            )
        )
        await db_session.flush()

        with pytest.raises(HTTPException) as excinfo:
            await _ensure_not_last_admin(
                db_session,
                default_tenant.id,
                removing_user_id=solo_admin.id,
                admin_role_id=admin_role.id,
            )
        assert excinfo.value.status_code == 409

    async def test_ensure_not_last_admin_allows_when_others_exist(
        self, db_session, default_tenant
    ):
        from core.db.models.user.role import Role
        from core.db.models.user.user import User
        from core.db.models.user.user_role import UserRole
        from routes.admin.users import _ensure_not_last_admin

        admin_role = Role(
            slug=f"adm-{uuid4().hex[:6]}",
            name=f"Adm {uuid4().hex[:6]}",
            is_system=True,
            tenant_id=None,
        )
        db_session.add(admin_role)
        await db_session.flush()

        a = User(
            email=f"a-{uuid4().hex[:6]}@test.magnet.ai",
            name="A",
            is_active=True,
            tenant_id=default_tenant.id,
        )
        b = User(
            email=f"b-{uuid4().hex[:6]}@test.magnet.ai",
            name="B",
            is_active=True,
            tenant_id=default_tenant.id,
        )
        db_session.add_all([a, b])
        await db_session.flush()
        db_session.add_all(
            [
                UserRole(
                    user_id=a.id,
                    role_id=admin_role.id,
                    assigned_at=datetime.now(UTC),
                ),
                UserRole(
                    user_id=b.id,
                    role_id=admin_role.id,
                    assigned_at=datetime.now(UTC),
                ),
            ]
        )
        await db_session.flush()

        # Removing one is allowed because the other remains.
        await _ensure_not_last_admin(
            db_session,
            default_tenant.id,
            removing_user_id=a.id,
            admin_role_id=admin_role.id,
        )


@pytest.mark.integration
class TestAccessLogHelpers:
    async def test_audit_log_query_filters_by_tenant(self, db_session, default_tenant):
        """Audit-log reads only the caller's tenant."""
        from core.db.models.audit import AccessAuditLog
        from core.db.models.tenant.tenant import Tenant
        from services.access_control import write_audit_log

        other = Tenant(slug=f"other-{uuid4().hex[:6]}", name="Other")
        db_session.add(other)
        await db_session.flush()

        # Write one row per tenant.
        await write_audit_log(
            db_session,
            tenant_id=default_tenant.id,
            actor_id=None,
            action="x",
            target_type="t",
            payload={},
        )
        await write_audit_log(
            db_session,
            tenant_id=other.id,
            actor_id=None,
            action="x",
            target_type="t",
            payload={},
        )

        rows = (
            (
                await db_session.execute(
                    select(AccessAuditLog).where(
                        AccessAuditLog.tenant_id == default_tenant.id
                    )
                )
            )
            .scalars()
            .all()
        )
        assert len(rows) == 1
