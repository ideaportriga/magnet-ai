"""Integration tests for PR 6 — tenant-scoped user groups.

- Group requires a tenant_id (NOT NULL).
- Two tenants can each have a group named "Project X".
- Same tenant rejects duplicate slug/name.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import select


@pytest.mark.integration
class TestGroupTenantScope:
    async def test_group_requires_tenant_id(self, db_session):
        from core.db.models.user.group import Group
        from core.db.rls_context import rls_context_scope

        # Clear contextvar so the before_flush safety net doesn't auto-fill.
        with rls_context_scope(tenant_id=None):
            bad = Group(
                slug=f"no-tenant-{uuid4().hex[:6]}",
                name=f"No tenant {uuid4().hex[:6]}",
            )
            db_session.add(bad)
            with pytest.raises(Exception):
                await db_session.flush()
            await db_session.rollback()

    async def test_two_tenants_share_slug(self, db_session, default_tenant):
        from core.db.models.tenant.tenant import Tenant
        from core.db.models.user.group import Group

        other = Tenant(slug=f"other-{uuid4().hex[:6]}", name="Other")
        db_session.add(other)
        await db_session.flush()

        slug = f"project-{uuid4().hex[:6]}"
        name = f"Project {uuid4().hex[:6]}"
        a = Group(tenant_id=default_tenant.id, slug=slug, name=name)
        b = Group(tenant_id=other.id, slug=slug, name=f"{name} 2")
        db_session.add_all([a, b])
        await db_session.flush()

        rows = (
            (await db_session.execute(select(Group).where(Group.slug == slug)))
            .scalars()
            .all()
        )
        assert {r.tenant_id for r in rows} == {default_tenant.id, other.id}

    async def test_duplicate_slug_in_same_tenant_rejected(
        self, db_session, default_tenant
    ):
        from core.db.models.user.group import Group

        slug = f"dup-{uuid4().hex[:6]}"
        db_session.add(
            Group(
                tenant_id=default_tenant.id,
                slug=slug,
                name=f"D {slug}",
            )
        )
        await db_session.flush()

        db_session.add(
            Group(
                tenant_id=default_tenant.id,
                slug=slug,
                name=f"D2 {slug}",
            )
        )
        with pytest.raises(Exception):
            await db_session.flush()
        await db_session.rollback()

    async def test_duplicate_name_in_same_tenant_rejected(
        self, db_session, default_tenant
    ):
        from core.db.models.user.group import Group

        name = f"Same Name {uuid4().hex[:6]}"
        db_session.add(
            Group(
                tenant_id=default_tenant.id,
                slug=f"a-{uuid4().hex[:6]}",
                name=name,
            )
        )
        await db_session.flush()

        db_session.add(
            Group(
                tenant_id=default_tenant.id,
                slug=f"b-{uuid4().hex[:6]}",
                name=name,
            )
        )
        with pytest.raises(Exception):
            await db_session.flush()
        await db_session.rollback()
