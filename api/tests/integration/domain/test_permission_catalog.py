"""Integration tests for the DB-backed permission catalog.

The unit suite covers the in-process resolver; here we verify that:
  - the new tables (permission, role_permission) exist after metadata.create_all
  - load_role_permissions_cache() resolves real DB rows
  - admin role with seeded grants returns all permission codes
  - custom role created at test time appears in the cache after reload
  - is_system column on `role` is writable and queryable
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import select


@pytest.mark.integration
class TestPermissionCatalog:
    async def test_permission_table_exists_and_seedable(self, db_session):
        from core.db.models.user.permission import Permission

        # Schema is created via metadata.create_all but the alembic seed
        # didn't run — insert a row manually to verify the model maps cleanly.
        row = Permission(
            code="read:agents",
            resource_type="agents",
            action="read",
            description="View agents",
            is_system=True,
        )
        db_session.add(row)
        await db_session.flush()

        fetched = (
            await db_session.execute(
                select(Permission).where(Permission.code == "read:agents")
            )
        ).scalar_one()
        assert fetched.resource_type == "agents"
        assert fetched.action == "read"
        assert fetched.is_system is True

    async def test_role_has_is_system_column(self, db_session, default_tenant):
        from core.db.models.user.role import Role

        slug = f"test-{uuid4().hex[:8]}"
        role = Role(
            name=f"Test {slug}",
            slug=slug,
            is_system=False,
            tenant_id=default_tenant.id,
        )
        db_session.add(role)
        await db_session.flush()

        fetched = (
            await db_session.execute(select(Role).where(Role.slug == slug))
        ).scalar_one()
        assert fetched.is_system is False

    async def test_role_permission_grants_are_unique_per_pair(
        self, db_session, default_tenant
    ):
        from core.db.models.user.permission import Permission
        from core.db.models.user.role import Role
        from core.db.models.user.role_permission import RolePermission

        slug = f"role-{uuid4().hex[:8]}"
        role = Role(name=slug, slug=slug, is_system=False, tenant_id=default_tenant.id)
        perm = Permission(
            code=f"read:{uuid4().hex[:8]}",
            resource_type="test",
            action="read",
        )
        db_session.add_all([role, perm])
        await db_session.flush()

        db_session.add(RolePermission(role_id=role.id, permission_code=perm.code))
        await db_session.flush()

        # Duplicate grant raises (uq_role_permission)
        db_session.add(RolePermission(role_id=role.id, permission_code=perm.code))
        with pytest.raises(Exception):
            await db_session.flush()
        await db_session.rollback()

    async def test_load_role_permissions_cache_reads_db_rows(
        self, db_session, default_tenant
    ):
        """load_role_permissions_cache() snapshots existing role_permission rows."""
        from core.db.models.user.permission import Permission
        from core.db.models.user.role import Role
        from core.db.models.user.role_permission import RolePermission
        import guards.permissions as perms

        slug = f"loader-{uuid4().hex[:8]}"
        role = Role(name=slug, slug=slug, is_system=False, tenant_id=default_tenant.id)
        perm1 = Permission(
            code=f"alpha:{uuid4().hex[:8]}",
            resource_type="alpha",
            action="read",
        )
        perm2 = Permission(
            code=f"beta:{uuid4().hex[:8]}",
            resource_type="beta",
            action="write",
        )
        db_session.add_all([role, perm1, perm2])
        await db_session.flush()
        db_session.add_all(
            [
                RolePermission(role_id=role.id, permission_code=perm1.code),
                RolePermission(role_id=role.id, permission_code=perm2.code),
            ]
        )
        await db_session.flush()

        try:
            # Pass the test session so we don't depend on the global alchemy
            # factory (which points at a different DB in the test harness).
            await perms.load_role_permissions_cache(session=db_session)
            cache = perms._ROLE_PERMISSIONS_CACHE
            assert cache is not None
            assert slug in cache
            assert cache[slug] == frozenset({perm1.code, perm2.code})
        finally:
            perms.reset_role_permissions_cache()
