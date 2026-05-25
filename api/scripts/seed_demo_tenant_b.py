#!/usr/bin/env python3
"""Seed a SECOND tenant + users for demonstrating tenant isolation.

Idempotent — safe to re-run.

Creates:
  Tenant `demo-b` (display name "Demo Co B")
  Department `core` inside that tenant
  Three users (all share DEV_SEED_PASSWORD, default `magnet-dev-12345`):
    admin-b@local.dev   — system `admin` role,  dept `core` (lead)
    user-b@local.dev    — system `user`  role,  dept `core`
    viewer-b@local.dev  — system `viewer` role, dept `core`
  One sample agent inside demo-b:
    agent-b-public — visibility=tenant, owner=admin-b

The point of this fixture is to prove tenant isolation:
  - admin-b cannot see anything inside the `default` tenant.
  - admin@local.dev (default tenant admin) cannot see anything inside `demo-b`.
  - Only super@local.dev (cross-tenant superuser) sees both.

Usage:
    cd api && uv run python scripts/seed_demo_tenant_b.py

Override password with DEV_SEED_PASSWORD env var (same convention as the
main seed_dev_fixtures.py).
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from uuid import UUID

SRC_PATH = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_PATH))

from config.config import load_env  # noqa: E402

load_env()

from sqlalchemy import select  # noqa: E402

from core.config.app import alchemy  # noqa: E402
from core.db.models.agent.agent import Agent  # noqa: E402
from core.db.models.department.department import Department  # noqa: E402
from core.db.models.department.user_department import UserDepartment  # noqa: E402
from core.db.models.tenant.tenant import Tenant  # noqa: E402
from core.db.models.user.role import Role  # noqa: E402
from core.db.models.user.user import User  # noqa: E402
from core.db.models.user.user_role import UserRole  # noqa: E402
from core.db.rls_context import apply_session_rls  # noqa: E402
from services.users.password import hash_password_async  # noqa: E402


DEFAULT_PASSWORD = os.environ.get("DEV_SEED_PASSWORD", "magnet-dev-12345")

TENANT_SLUG = "demo-b"
TENANT_NAME = "Demo Co B"

DEPARTMENT = {"slug": "core", "name": "Core"}

TEST_USERS = [
    {
        "email": "admin-b@local.dev",
        "name": "Demo-B Admin",
        "role_slug": "admin",
        "is_lead": True,
    },
    {
        "email": "user-b@local.dev",
        "name": "Demo-B User",
        "role_slug": "user",
    },
    {
        "email": "viewer-b@local.dev",
        "name": "Demo-B Viewer",
        "role_slug": "viewer",
    },
]


async def _get_or_create_tenant(session) -> tuple[Tenant, bool]:
    tenant = (
        await session.execute(select(Tenant).where(Tenant.slug == TENANT_SLUG))
    ).scalar_one_or_none()
    if tenant is not None:
        return tenant, False
    tenant = Tenant(slug=TENANT_SLUG, name=TENANT_NAME, is_active=True)
    session.add(tenant)
    await session.flush()
    return tenant, True


async def _get_or_create_user(session, *, email, name, tenant_id) -> tuple[User, bool]:
    user = (
        await session.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()
    if user is not None:
        return user, False
    user = User(
        email=email,
        name=name,
        hashed_password=await hash_password_async(DEFAULT_PASSWORD),
        is_active=True,
        is_verified=True,
        is_superuser=False,
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
    agent = Agent(
        name=name,
        system_name=system_name,
        tenant_id=tenant_id,
        owner_id=owner_id,
        department_id=None,
        visibility=visibility,
        category="default",
        active_variant=None,
        variants=[],
        channels={},
    )
    session.add(agent)
    await session.flush()
    return agent


async def main() -> None:
    print("Seeding demo tenant B…")
    print(f"  password = {DEFAULT_PASSWORD!r}")
    async with alchemy.get_session() as session:
        tenant, created = await _get_or_create_tenant(session)
        tag = "created" if created else "exists"
        print(f"  tenant   = {tenant.slug} ({tenant.id}) [{tag}]")

        await apply_session_rls(session, tenant_id=str(tenant.id))

        roles_by_slug: dict[str, Role] = {}
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

        dept = await _ensure_department(
            session,
            tenant_id=tenant.id,
            slug=DEPARTMENT["slug"],
            name=DEPARTMENT["name"],
        )
        print(f"  dept     = {dept.slug}")

        users_by_email: dict[str, User] = {}
        for spec in TEST_USERS:
            user, was_created = await _get_or_create_user(
                session,
                email=spec["email"],
                name=spec["name"],
                tenant_id=tenant.id,
            )
            users_by_email[user.email] = user
            role = roles_by_slug[spec["role_slug"]]
            assigned = await _ensure_role_assigned(
                session, user_id=user.id, role_id=role.id
            )
            await _ensure_membership(
                session,
                tenant_id=tenant.id,
                user_id=user.id,
                department_id=dept.id,
                is_lead=spec.get("is_lead", False),
            )
            tag = "created" if was_created else "exists"
            lead_tag = " (lead)" if spec.get("is_lead") else ""
            print(
                f"  user     = {user.email} [{tag}] role={spec['role_slug']} "
                f"dept={dept.slug}{lead_tag}"
                f"{' (role assigned)' if assigned else ''}"
            )

        admin_b = users_by_email["admin-b@local.dev"]
        agent = await _ensure_agent(
            session,
            tenant_id=tenant.id,
            system_name="agent-b-public",
            name="Demo-B Public Agent",
            owner_id=admin_b.id,
            visibility="tenant",
        )
        print(f"  agent    = {agent.system_name}")

        await session.commit()

    print("\n✅ Demo-B seed done.")
    print("Try logging in via /api/v2/auth/login with any of:")
    for spec in TEST_USERS:
        print(
            f"  {spec['email']:24s} password={DEFAULT_PASSWORD!r}  "
            f"role={spec['role_slug']:10s} tenant={TENANT_SLUG}"
        )


if __name__ == "__main__":
    asyncio.run(main())
