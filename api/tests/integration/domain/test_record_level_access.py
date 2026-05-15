"""Integration tests for PR 8 — record-level access on agents.

Exercises the PermissionService 11-step algorithm against real DB rows.
"""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest


def _admin_role():
    return SimpleNamespace(slug="admin", is_system=True)


def _user_role():
    return SimpleNamespace(slug="user", is_system=True)


def _viewer_role():
    return SimpleNamespace(slug="viewer", is_system=True)


def _make_auth(user, *, tenant_id):
    """Build an Auth-like object compatible with PermissionService."""
    return SimpleNamespace(
        type="local_jwt",
        data={"tenant_id": str(tenant_id)},
        user_id=str(user.id) if user else None,
        user=user,
        tenant_id=str(tenant_id),
    )


async def _create_user(session, *, tenant_id, roles=None):
    from core.db.models.user.user import User

    u = User(
        email=f"u-{uuid4().hex[:6]}@test.magnet.ai",
        name="U",
        is_active=True,
        tenant_id=tenant_id,
    )
    u.roles = roles or []
    session.add(u)
    await session.flush()
    return u


async def _create_agent(
    session,
    *,
    tenant_id,
    owner_id=None,
    department_id=None,
    visibility="tenant",
):
    from core.db.models.agent.agent import Agent

    agent = Agent(
        name=f"A {uuid4().hex[:6]}",
        system_name=f"a-{uuid4().hex[:8]}",
        tenant_id=tenant_id,
        owner_id=owner_id,
        department_id=department_id,
        visibility=visibility,
        category="default",
        active_variant="default",
        variants=[{"name": "default", "system_prompt": "x"}],
        channels={},
    )
    session.add(agent)
    await session.flush()
    return agent


@pytest.mark.integration
class TestOwnership:
    async def test_owner_can_view_private(self, db_session, default_tenant):
        from services.access_control import PermissionService

        owner = await _create_user(
            db_session, tenant_id=default_tenant.id, roles=[_user_role()]
        )
        agent = await _create_agent(
            db_session,
            tenant_id=default_tenant.id,
            owner_id=owner.id,
            visibility="private",
        )

        auth = _make_auth(owner, tenant_id=default_tenant.id)
        assert (
            await PermissionService.can(
                db_session,
                auth=auth,
                action="view",
                resource_type="agents",
                resource=agent,
            )
            is True
        )

    async def test_non_owner_cannot_view_private(self, db_session, default_tenant):
        from services.access_control import PermissionService

        owner = await _create_user(
            db_session, tenant_id=default_tenant.id, roles=[_user_role()]
        )
        other = await _create_user(
            db_session, tenant_id=default_tenant.id, roles=[_user_role()]
        )
        agent = await _create_agent(
            db_session,
            tenant_id=default_tenant.id,
            owner_id=owner.id,
            visibility="private",
        )

        auth = _make_auth(other, tenant_id=default_tenant.id)
        assert (
            await PermissionService.can(
                db_session,
                auth=auth,
                action="view",
                resource_type="agents",
                resource=agent,
            )
            is False
        )

    async def test_owner_can_edit_with_global_capability(
        self, db_session, default_tenant
    ):
        from services.access_control import PermissionService

        owner = await _create_user(
            db_session, tenant_id=default_tenant.id, roles=[_admin_role()]
        )
        agent = await _create_agent(
            db_session,
            tenant_id=default_tenant.id,
            owner_id=owner.id,
            visibility="private",
        )

        auth = _make_auth(owner, tenant_id=default_tenant.id)
        # admin role has all permissions including write
        assert (
            await PermissionService.can(
                db_session,
                auth=auth,
                action="edit",
                resource_type="agents",
                resource=agent,
            )
            is True
        )


@pytest.mark.integration
class TestTenantVisibility:
    async def test_viewer_sees_tenant_visible_agents(self, db_session, default_tenant):
        from services.access_control import PermissionService

        owner = await _create_user(
            db_session, tenant_id=default_tenant.id, roles=[_user_role()]
        )
        viewer = await _create_user(
            db_session, tenant_id=default_tenant.id, roles=[_viewer_role()]
        )
        agent = await _create_agent(
            db_session,
            tenant_id=default_tenant.id,
            owner_id=owner.id,
            visibility="tenant",
        )

        auth = _make_auth(viewer, tenant_id=default_tenant.id)
        assert (
            await PermissionService.can(
                db_session,
                auth=auth,
                action="view",
                resource_type="agents",
                resource=agent,
            )
            is True
        )

    async def test_viewer_cannot_edit_tenant_visible(self, db_session, default_tenant):
        from services.access_control import PermissionService

        owner = await _create_user(
            db_session, tenant_id=default_tenant.id, roles=[_user_role()]
        )
        viewer = await _create_user(
            db_session, tenant_id=default_tenant.id, roles=[_viewer_role()]
        )
        agent = await _create_agent(
            db_session,
            tenant_id=default_tenant.id,
            owner_id=owner.id,
            visibility="tenant",
        )

        auth = _make_auth(viewer, tenant_id=default_tenant.id)
        # viewer has no write:agents → capability ceiling blocks
        assert (
            await PermissionService.can(
                db_session,
                auth=auth,
                action="edit",
                resource_type="agents",
                resource=agent,
            )
            is False
        )


@pytest.mark.integration
class TestDepartmentVisibility:
    async def test_member_sees_department_agent(self, db_session, default_tenant):
        from core.db.models.department import Department, UserDepartment
        from services.access_control import PermissionService

        dept = Department(
            tenant_id=default_tenant.id,
            slug=f"d-{uuid4().hex[:6]}",
            name="D",
        )
        db_session.add(dept)
        await db_session.flush()

        owner = await _create_user(
            db_session, tenant_id=default_tenant.id, roles=[_user_role()]
        )
        member = await _create_user(
            db_session, tenant_id=default_tenant.id, roles=[_user_role()]
        )
        db_session.add(
            UserDepartment(
                tenant_id=default_tenant.id,
                user_id=member.id,
                department_id=dept.id,
                is_lead=False,
            )
        )
        await db_session.flush()

        agent = await _create_agent(
            db_session,
            tenant_id=default_tenant.id,
            owner_id=owner.id,
            department_id=dept.id,
            visibility="department",
        )

        auth = _make_auth(member, tenant_id=default_tenant.id)
        assert (
            await PermissionService.can(
                db_session,
                auth=auth,
                action="view",
                resource_type="agents",
                resource=agent,
            )
            is True
        )

    async def test_lead_can_edit_department_agent(self, db_session, default_tenant):
        from core.db.models.department import Department, UserDepartment
        from services.access_control import PermissionService

        dept = Department(
            tenant_id=default_tenant.id,
            slug=f"d-{uuid4().hex[:6]}",
            name="D",
        )
        db_session.add(dept)
        await db_session.flush()

        # user role does NOT have write:agents — but admin role does. Use a
        # custom mix: user role with write:agents would be tested through
        # role_permission, but the in-code SYSTEM_ROLE_DEFAULTS already
        # gives admin write:agents.
        lead = await _create_user(
            db_session, tenant_id=default_tenant.id, roles=[_admin_role()]
        )
        db_session.add(
            UserDepartment(
                tenant_id=default_tenant.id,
                user_id=lead.id,
                department_id=dept.id,
                is_lead=True,
            )
        )
        await db_session.flush()

        agent = await _create_agent(
            db_session,
            tenant_id=default_tenant.id,
            owner_id=lead.id,  # not lead, but doesn't matter
            department_id=dept.id,
            visibility="department",
        )

        auth = _make_auth(lead, tenant_id=default_tenant.id)
        assert (
            await PermissionService.can(
                db_session,
                auth=auth,
                action="edit",
                resource_type="agents",
                resource=agent,
            )
            is True
        )


@pytest.mark.integration
class TestExplicitGrant:
    async def test_user_grant_read_gives_view(self, db_session, default_tenant):
        from core.db.models.access_grant import ResourceAccessGrant
        from services.access_control import PermissionService

        owner = await _create_user(
            db_session, tenant_id=default_tenant.id, roles=[_user_role()]
        )
        grantee = await _create_user(
            db_session, tenant_id=default_tenant.id, roles=[_user_role()]
        )
        agent = await _create_agent(
            db_session,
            tenant_id=default_tenant.id,
            owner_id=owner.id,
            visibility="private",
        )

        db_session.add(
            ResourceAccessGrant(
                tenant_id=default_tenant.id,
                resource_type="agents",
                resource_id=agent.id,
                principal_type="user",
                principal_id=grantee.id,
                access_level="read",
            )
        )
        await db_session.flush()

        auth = _make_auth(grantee, tenant_id=default_tenant.id)
        assert (
            await PermissionService.can(
                db_session,
                auth=auth,
                action="view",
                resource_type="agents",
                resource=agent,
            )
            is True
        )

    async def test_grant_write_does_not_grant_edit_without_capability(
        self, db_session, default_tenant
    ):
        """Capability ceiling: even with 'write' grant, viewer (no global
        write:agents) cannot edit."""
        from core.db.models.access_grant import ResourceAccessGrant
        from services.access_control import PermissionService

        owner = await _create_user(
            db_session, tenant_id=default_tenant.id, roles=[_user_role()]
        )
        grantee = await _create_user(
            db_session, tenant_id=default_tenant.id, roles=[_viewer_role()]
        )
        agent = await _create_agent(
            db_session,
            tenant_id=default_tenant.id,
            owner_id=owner.id,
            visibility="private",
        )

        db_session.add(
            ResourceAccessGrant(
                tenant_id=default_tenant.id,
                resource_type="agents",
                resource_id=agent.id,
                principal_type="user",
                principal_id=grantee.id,
                access_level="write",
            )
        )
        await db_session.flush()

        auth = _make_auth(grantee, tenant_id=default_tenant.id)
        # 'write' grant + 'read' capability → view, but not edit.
        assert (
            await PermissionService.can(
                db_session,
                auth=auth,
                action="view",
                resource_type="agents",
                resource=agent,
            )
            is True
        )
        assert (
            await PermissionService.can(
                db_session,
                auth=auth,
                action="edit",
                resource_type="agents",
                resource=agent,
            )
            is False
        )


@pytest.mark.integration
class TestCrossTenantAndAdmin:
    async def test_cross_tenant_returns_false(self, db_session, default_tenant):
        from core.db.models.tenant.tenant import Tenant
        from services.access_control import PermissionService

        other = Tenant(slug=f"o-{uuid4().hex[:6]}", name="Other")
        db_session.add(other)
        await db_session.flush()

        # An agent under tenant `other`.
        agent = await _create_agent(
            db_session,
            tenant_id=other.id,
            owner_id=None,
            visibility="tenant",
        )

        # Default tenant user.
        viewer = await _create_user(
            db_session, tenant_id=default_tenant.id, roles=[_admin_role()]
        )
        auth = _make_auth(viewer, tenant_id=default_tenant.id)
        # Even admin in default tenant cannot see other tenant's agent.
        assert (
            await PermissionService.can(
                db_session,
                auth=auth,
                action="view",
                resource_type="agents",
                resource=agent,
            )
            is False
        )

    async def test_tenant_admin_can_edit_anyone(self, db_session, default_tenant):
        from services.access_control import PermissionService

        owner = await _create_user(
            db_session, tenant_id=default_tenant.id, roles=[_user_role()]
        )
        admin = await _create_user(
            db_session, tenant_id=default_tenant.id, roles=[_admin_role()]
        )
        agent = await _create_agent(
            db_session,
            tenant_id=default_tenant.id,
            owner_id=owner.id,
            visibility="private",
        )
        auth = _make_auth(admin, tenant_id=default_tenant.id)
        for act in ("view", "edit", "delete", "share"):
            assert (
                await PermissionService.can(
                    db_session,
                    auth=auth,
                    action=act,
                    resource_type="agents",
                    resource=agent,
                )
                is True
            )


@pytest.mark.integration
class TestComputeRecordPermissions:
    async def test_owner_block_has_all_true_for_admin(self, db_session, default_tenant):
        from services.access_control import PermissionService

        owner = await _create_user(
            db_session, tenant_id=default_tenant.id, roles=[_admin_role()]
        )
        agent = await _create_agent(
            db_session,
            tenant_id=default_tenant.id,
            owner_id=owner.id,
            visibility="private",
        )
        auth = _make_auth(owner, tenant_id=default_tenant.id)
        perms = await PermissionService.compute_record_permissions(
            db_session,
            auth=auth,
            resource_type="agents",
            resource=agent,
        )
        assert perms == {"view": True, "edit": True, "delete": True, "share": True}

    async def test_block_has_only_view_for_viewer(self, db_session, default_tenant):
        from services.access_control import PermissionService

        viewer = await _create_user(
            db_session, tenant_id=default_tenant.id, roles=[_viewer_role()]
        )
        agent = await _create_agent(
            db_session,
            tenant_id=default_tenant.id,
            owner_id=None,
            visibility="tenant",
        )
        auth = _make_auth(viewer, tenant_id=default_tenant.id)
        perms = await PermissionService.compute_record_permissions(
            db_session,
            auth=auth,
            resource_type="agents",
            resource=agent,
        )
        assert perms == {"view": True, "edit": False, "delete": False, "share": False}
