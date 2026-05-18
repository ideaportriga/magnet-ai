#!/usr/bin/env python3
"""Seed test users, custom roles and sample agents for local dev.

Idempotent — safe to re-run. Creates everything inside the `default` tenant
(which is itself created by migrations).

Test accounts (all use the same dev password — see DEFAULT_PASSWORD below):

    super@local.dev     — is_superuser=True, cross-tenant god mode.
    admin@local.dev     — system `admin` role, dept `executive` (lead).
    user@local.dev      — system `user` role, dept `platform`.
    viewer@local.dev    — system `viewer` role, dept `qa`.
    curator@local.dev   — custom role `kg-curator`, dept `knowledge`.

All sit in the `default` tenant (= "organization" in this schema —
Tenant IS the org boundary; there is no separate Organization table).

Sample data (after a fresh run):
  - Tenant `default` (created here if migrations did not).
  - Departments: `executive`, `platform`, `qa`, `knowledge`.
  - Three agents:
      `agent-public`  — visibility=tenant, owner=admin
      `agent-team`    — visibility=department(platform), owner=admin
      `agent-private` — visibility=private, owner=admin
        (with explicit `read` grant for `viewer@local.dev`)

Usage:
    cd api && poetry run python scripts/seed_dev_fixtures.py

Required env (loaded via .env / config.config.load_env if available):
    DATABASE_URL or the standard alchemy config

Override password with DEV_SEED_PASSWORD env var. Default is `magnet-dev-12345`.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from uuid import UUID

# Add src/ to sys.path BEFORE importing app modules.
SRC_PATH = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_PATH))

from config.config import load_env  # noqa: E402

load_env()

from sqlalchemy import select  # noqa: E402

from core.config.app import alchemy  # noqa: E402
from core.db.models.access_grant import ResourceAccessGrant  # noqa: E402
from core.db.models.agent.agent import Agent  # noqa: E402
from core.db.models.department.department import Department  # noqa: E402
from core.db.models.department.user_department import UserDepartment  # noqa: E402
from core.db.models.tenant.tenant import Tenant  # noqa: E402
from core.db.models.user.permission import Permission as PermissionModel  # noqa: E402
from core.db.models.user.role import Role  # noqa: E402
from core.db.models.user.role_permission import RolePermission  # noqa: E402
from core.db.models.user.user import User  # noqa: E402
from core.db.models.user.user_role import UserRole  # noqa: E402
from core.db.rls_context import apply_session_rls  # noqa: E402
from guards.permissions import (  # noqa: E402
    Permission as PermissionCode,
    load_role_permissions_cache,
)
from services.users.password import hash_password_async  # noqa: E402


DEFAULT_PASSWORD = os.environ.get("DEV_SEED_PASSWORD", "magnet-dev-12345")


TEST_USERS = [
    {
        "email": "super@local.dev",
        "name": "Dev Superuser",
        "role_slug": "admin",  # role membership is moot — superuser bypasses
        "is_superuser": True,  # cross-tenant god mode
        "department_slug": "executive",
        "is_lead": True,
    },
    {
        "email": "admin@local.dev",
        "name": "Dev Admin",
        "role_slug": "admin",
        "is_superuser": False,  # NOT a platform superuser — tenant admin.
        "department_slug": "executive",
        "is_lead": True,
    },
    {
        "email": "user@local.dev",
        "name": "Dev User",
        "role_slug": "user",
        "department_slug": "platform",
    },
    {
        "email": "viewer@local.dev",
        "name": "Dev Viewer",
        "role_slug": "viewer",
        "department_slug": "qa",
    },
    {
        "email": "curator@local.dev",
        "name": "Knowledge Curator",
        "role_slug": "kg-curator",  # custom role created below
        "department_slug": "knowledge",
    },
]


DEPARTMENTS = [
    {"slug": "executive", "name": "Executive"},
    {"slug": "platform", "name": "Platform"},
    {"slug": "qa", "name": "QA"},
    {"slug": "knowledge", "name": "Knowledge"},
]


CUSTOM_ROLE = {
    "slug": "kg-curator",
    "name": "Knowledge Curator",
    "description": "Read agents; full access to collections and KG.",
    "permissions": [
        PermissionCode.AGENTS_READ.value,
        PermissionCode.COLLECTIONS_READ.value,
        PermissionCode.COLLECTIONS_WRITE.value,
        PermissionCode.COLLECTIONS_DELETE.value,
        PermissionCode.KNOWLEDGE_GRAPH_READ.value,
        PermissionCode.KNOWLEDGE_GRAPH_WRITE.value,
        PermissionCode.KNOWLEDGE_GRAPH_DELETE.value,
    ],
}


async def _get_or_create_default_tenant(session) -> tuple[Tenant, bool]:
    tenant = (
        await session.execute(select(Tenant).where(Tenant.slug == "default"))
    ).scalar_one_or_none()
    if tenant is not None:
        return tenant, False
    tenant = Tenant(slug="default", name="Default", is_active=True)
    session.add(tenant)
    await session.flush()
    return tenant, True


async def _get_or_create_user(
    session, *, email, name, tenant_id, is_superuser: bool = False
) -> tuple[User, bool]:
    user = (
        await session.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()
    if user is not None:
        # Keep the superuser flag in sync with the spec on re-runs.
        if user.is_superuser != is_superuser:
            user.is_superuser = is_superuser
            await session.flush()
        return user, False
    user = User(
        email=email,
        name=name,
        hashed_password=await hash_password_async(DEFAULT_PASSWORD),
        is_active=True,
        is_verified=True,
        is_superuser=is_superuser,
        tenant_id=tenant_id,
    )
    session.add(user)
    await session.flush()
    return user, True


async def _ensure_role_assigned(session, *, user_id: UUID, role_id: UUID) -> bool:
    existing = (
        await session.execute(
            select(UserRole).where(
                UserRole.user_id == user_id, UserRole.role_id == role_id
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        return False
    session.add(UserRole(user_id=user_id, role_id=role_id))
    await session.flush()
    return True


async def _get_or_create_custom_role(session, *, tenant_id) -> Role:
    role = (
        await session.execute(
            select(Role).where(
                Role.slug == CUSTOM_ROLE["slug"], Role.tenant_id == tenant_id
            )
        )
    ).scalar_one_or_none()
    if role is None:
        role = Role(
            slug=CUSTOM_ROLE["slug"],
            name=CUSTOM_ROLE["name"],
            description=CUSTOM_ROLE["description"],
            is_system=False,
            tenant_id=tenant_id,
        )
        session.add(role)
        await session.flush()

    # Ensure permissions are seeded.
    existing_codes = {
        r[0]
        for r in (
            await session.execute(
                select(RolePermission.permission_code).where(
                    RolePermission.role_id == role.id
                )
            )
        ).all()
    }
    for code in CUSTOM_ROLE["permissions"]:
        # Only attach permissions that exist in the catalog.
        present = (
            await session.execute(
                select(PermissionModel.code).where(PermissionModel.code == code)
            )
        ).scalar_one_or_none()
        if present is None:
            print(f"  ⚠️  permission {code} not in catalog — skipped")
            continue
        if code not in existing_codes:
            session.add(RolePermission(role_id=role.id, permission_code=code))
    await session.flush()
    return role


async def _ensure_department(session, *, tenant_id, slug: str, name: str) -> Department:
    dept = (
        await session.execute(
            select(Department).where(
                Department.tenant_id == tenant_id, Department.slug == slug
            )
        )
    ).scalar_one_or_none()
    if dept is None:
        dept = Department(tenant_id=tenant_id, slug=slug, name=name)
        session.add(dept)
        await session.flush()
    return dept


async def _ensure_membership(
    session, *, tenant_id, user_id, department_id, is_lead: bool = False
):
    membership = (
        await session.execute(
            select(UserDepartment).where(
                UserDepartment.user_id == user_id,
                UserDepartment.department_id == department_id,
            )
        )
    ).scalar_one_or_none()
    if membership is None:
        session.add(
            UserDepartment(
                tenant_id=tenant_id,
                user_id=user_id,
                department_id=department_id,
                is_lead=is_lead,
            )
        )
        await session.flush()
    elif membership.is_lead != is_lead:
        membership.is_lead = is_lead
        await session.flush()


async def _ensure_agent(
    session,
    *,
    tenant_id,
    system_name: str,
    name: str,
    owner_id: UUID,
    visibility: str,
    department_id=None,
) -> Agent:
    agent = (
        await session.execute(
            select(Agent).where(
                Agent.tenant_id == tenant_id,
                Agent.system_name == system_name,
            )
        )
    ).scalar_one_or_none()
    if agent is not None:
        return agent
    # Variants left empty — full `EntityVariant[AgentVariantValue]` structure
    # is non-trivial and not needed for permission-check demos. UI/admin
    # tests work with empty variants.
    agent = Agent(
        name=name,
        system_name=system_name,
        tenant_id=tenant_id,
        owner_id=owner_id,
        department_id=department_id,
        visibility=visibility,
        category="default",
        active_variant=None,
        variants=[],
        channels={},
    )
    session.add(agent)
    await session.flush()
    return agent


async def _ensure_grant(
    session,
    *,
    tenant_id,
    resource_type: str,
    resource_id: UUID,
    user_id: UUID,
    access_level: str,
):
    existing = (
        await session.execute(
            select(ResourceAccessGrant).where(
                ResourceAccessGrant.tenant_id == tenant_id,
                ResourceAccessGrant.resource_type == resource_type,
                ResourceAccessGrant.resource_id == resource_id,
                ResourceAccessGrant.principal_type == "user",
                ResourceAccessGrant.principal_id == user_id,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        return
    session.add(
        ResourceAccessGrant(
            tenant_id=tenant_id,
            resource_type=resource_type,
            resource_id=resource_id,
            principal_type="user",
            principal_id=user_id,
            access_level=access_level,
        )
    )
    await session.flush()


async def main() -> None:
    print("Seeding dev fixtures…")
    print(f"  password = {DEFAULT_PASSWORD!r}")
    async with alchemy.get_session() as session:
        tenant, tenant_created = await _get_or_create_default_tenant(session)
        tag = "created" if tenant_created else "exists"
        print(f"  tenant   = {tenant.slug} ({tenant.id}) [{tag}]")

        # RLS is on for agents — we need a GUC. Use the default tenant.
        await apply_session_rls(session, tenant_id=str(tenant.id))

        # 1. Custom role.
        custom_role = await _get_or_create_custom_role(session, tenant_id=tenant.id)
        print(
            f"  role     = {custom_role.slug} "
            f"({len(CUSTOM_ROLE['permissions'])} permissions)"
        )

        # System roles (admin, user, viewer) — already seeded by migration.
        roles_by_slug: dict[str, Role] = {custom_role.slug: custom_role}
        for slug in ("admin", "user", "viewer"):
            role = (
                await session.execute(
                    select(Role).where(Role.slug == slug, Role.is_system == True)  # noqa: E712
                )
            ).scalar_one_or_none()
            if role is None:
                raise RuntimeError(
                    f"System role '{slug}' missing — run migrations first."
                )
            roles_by_slug[slug] = role

        # 2. Departments.
        depts_by_slug: dict[str, Department] = {}
        for spec in DEPARTMENTS:
            dept = await _ensure_department(
                session, tenant_id=tenant.id, slug=spec["slug"], name=spec["name"]
            )
            depts_by_slug[dept.slug] = dept
        print(f"  depts    = {', '.join(depts_by_slug)}")

        # 3. Test users — each gets tenant + role + department membership.
        users_by_email: dict[str, User] = {}
        for spec in TEST_USERS:
            user, created = await _get_or_create_user(
                session,
                email=spec["email"],
                name=spec["name"],
                tenant_id=tenant.id,
                is_superuser=spec.get("is_superuser", False),
            )
            users_by_email[user.email] = user
            role = roles_by_slug[spec["role_slug"]]
            assigned = await _ensure_role_assigned(
                session, user_id=user.id, role_id=role.id
            )
            dept = depts_by_slug[spec["department_slug"]]
            await _ensure_membership(
                session,
                tenant_id=tenant.id,
                user_id=user.id,
                department_id=dept.id,
                is_lead=spec.get("is_lead", False),
            )
            tag = "created" if created else "exists"
            super_tag = " superuser" if spec.get("is_superuser") else ""
            lead_tag = " (lead)" if spec.get("is_lead") else ""
            print(
                f"  user     = {user.email} [{tag}] role={spec['role_slug']} "
                f"dept={dept.slug}{lead_tag}{super_tag}"
                f"{' (role assigned)' if assigned else ''}"
            )

        # 4. Sample agents with different visibility.
        admin = users_by_email["admin@local.dev"]
        viewer = users_by_email["viewer@local.dev"]
        platform_dept = depts_by_slug["platform"]

        a_public = await _ensure_agent(
            session,
            tenant_id=tenant.id,
            system_name="agent-public",
            name="Public Agent",
            owner_id=admin.id,
            visibility="tenant",
        )
        a_team = await _ensure_agent(
            session,
            tenant_id=tenant.id,
            system_name="agent-team",
            name="Team Agent",
            owner_id=admin.id,
            visibility="department",
            department_id=platform_dept.id,
        )
        a_private = await _ensure_agent(
            session,
            tenant_id=tenant.id,
            system_name="agent-private",
            name="Private Agent",
            owner_id=admin.id,
            visibility="private",
        )
        print(
            f"  agents   = {a_public.system_name} {a_team.system_name} {a_private.system_name}"
        )

        # 5. Explicit grant: viewer can read the private agent.
        await _ensure_grant(
            session,
            tenant_id=tenant.id,
            resource_type="agents",
            resource_id=a_private.id,
            user_id=viewer.id,
            access_level="read",
        )
        print(f"  grant    = viewer@local.dev → read({a_private.system_name})")

        await session.commit()

        # Reload permission cache so the new custom role's permissions are
        # picked up by the running process (if any).
        try:
            await load_role_permissions_cache()
        except Exception:
            pass

    print("\n✅ Seed done.")
    print("Try logging in via /api/v2/auth/login with any of:")
    for spec in TEST_USERS:
        print(
            f"  {spec['email']:24s} password={DEFAULT_PASSWORD!r}  "
            f"role={spec['role_slug']:10s} dept={spec['department_slug']}"
        )


if __name__ == "__main__":
    asyncio.run(main())
