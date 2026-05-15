"""Integration tests for PR 4: tenant base + role tenant_id invariants.

Schema reality checks against a real Postgres container:
  - default tenant is seeded by conftest
  - tenant_id is NOT NULL on user_account / api_keys
  - CHECK invariant on role rejects bad (is_system, tenant_id) combos
  - partial unique indexes let two tenants both have a 'reviewer' role
    while still rejecting a duplicate inside the same tenant
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import select


@pytest.mark.integration
class TestTenantBase:
    async def test_default_tenant_exists(self, db_session, default_tenant):
        assert default_tenant.slug == "default"
        assert default_tenant.is_active is True

    async def test_create_secondary_tenant(self, db_session):
        from core.db.models.tenant.tenant import Tenant

        slug = f"acme-{uuid4().hex[:6]}"
        t = Tenant(slug=slug, name="Acme")
        db_session.add(t)
        await db_session.flush()

        fetched = (
            await db_session.execute(select(Tenant).where(Tenant.slug == slug))
        ).scalar_one()
        assert fetched.id is not None

    async def test_user_requires_tenant_id(self, db_session):
        from core.db.models.user.user import User
        from core.db.rls_context import rls_context_scope

        # Missing tenant_id → IntegrityError on flush.
        # The before_flush safety net (`_populate_tenant_id`) auto-fills from
        # the contextvar, so clear it here to truly exercise the NOT NULL.
        with rls_context_scope(tenant_id=None):
            u = User(
                email=f"no-tenant-{uuid4().hex[:6]}@test.magnet.ai",
                name="N",
                is_active=True,
            )
            db_session.add(u)
            with pytest.raises(Exception):
                await db_session.flush()
            await db_session.rollback()


@pytest.mark.integration
class TestRoleTenantInvariant:
    async def test_system_role_with_tenant_id_rejected(
        self, db_session, default_tenant
    ):
        from core.db.models.user.role import Role

        # CHECK invariant: is_system=True must have tenant_id IS NULL.
        bad = Role(
            slug=f"sys-{uuid4().hex[:6]}",
            name=f"Sys {uuid4().hex[:6]}",
            is_system=True,
            tenant_id=default_tenant.id,  # disallowed for system roles
        )
        db_session.add(bad)
        with pytest.raises(Exception):
            await db_session.flush()
        await db_session.rollback()

    async def test_custom_role_without_tenant_id_rejected(self, db_session):
        from core.db.models.user.role import Role

        # CHECK invariant: is_system=False must have tenant_id IS NOT NULL.
        bad = Role(
            slug=f"cust-{uuid4().hex[:6]}",
            name=f"Cust {uuid4().hex[:6]}",
            is_system=False,
            tenant_id=None,
        )
        db_session.add(bad)
        with pytest.raises(Exception):
            await db_session.flush()
        await db_session.rollback()

    async def test_two_tenants_can_have_same_slug(self, db_session, default_tenant):
        from core.db.models.tenant.tenant import Tenant
        from core.db.models.user.role import Role

        # Make a second tenant so we can collide slugs across them.
        other = Tenant(slug=f"other-{uuid4().hex[:6]}", name="Other")
        db_session.add(other)
        await db_session.flush()

        slug = f"reviewer-{uuid4().hex[:6]}"
        name = f"Reviewer {uuid4().hex[:6]}"

        r1 = Role(slug=slug, name=name, is_system=False, tenant_id=default_tenant.id)
        r2 = Role(
            slug=slug,
            name=f"{name} 2",
            is_system=False,
            tenant_id=other.id,
        )
        db_session.add_all([r1, r2])
        await db_session.flush()  # both should commit

        rows = (
            (await db_session.execute(select(Role).where(Role.slug == slug)))
            .scalars()
            .all()
        )
        assert {r.tenant_id for r in rows} == {default_tenant.id, other.id}

    async def test_duplicate_slug_in_same_tenant_rejected(
        self, db_session, default_tenant
    ):
        from core.db.models.user.role import Role

        slug = f"dup-{uuid4().hex[:6]}"
        db_session.add(
            Role(
                slug=slug,
                name=f"D {slug}",
                is_system=False,
                tenant_id=default_tenant.id,
            )
        )
        await db_session.flush()

        db_session.add(
            Role(
                slug=slug,
                name=f"D2 {slug}",
                is_system=False,
                tenant_id=default_tenant.id,
            )
        )
        with pytest.raises(Exception):
            await db_session.flush()
        await db_session.rollback()
