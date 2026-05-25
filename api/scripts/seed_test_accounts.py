#!/usr/bin/env python3
"""Seed 4 test accounts across 2 tenants for end-to-end / QA testing.

Idempotent — safe to re-run.

Creates two fresh tenants (separate from `default` / `demo-b`) so QA can
exercise cross-tenant flows without polluting the existing dev fixtures:

    Tenant `qa-alpha` (display "QA Alpha")
        qa-alpha-admin@local.dev  — admin role, dept `core` (lead)
        qa-alpha-user@local.dev   — user  role, dept `core`

    Tenant `qa-beta`  (display "QA Beta")
        qa-beta-admin@local.dev   — admin role, dept `core` (lead)
        qa-beta-user@local.dev    — user  role, dept `core`

All four users share the same password (env override `QA_SEED_PASSWORD`,
default `magnet-qa-12345`). Companion file with the rendered credentials:
    docs/qa/test-accounts.md

Usage:
    cd api && uv run python scripts/seed_test_accounts.py
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
from core.db.models.department.department import Department  # noqa: E402
from core.db.models.department.user_department import UserDepartment  # noqa: E402
from core.db.models.tenant.tenant import Tenant  # noqa: E402
from core.db.models.user.role import Role  # noqa: E402
from core.db.models.user.user import User  # noqa: E402
from core.db.models.user.user_role import UserRole  # noqa: E402
from core.db.rls_context import apply_session_rls  # noqa: E402
from services.users.password import hash_password_async  # noqa: E402


DEFAULT_PASSWORD = os.environ.get("QA_SEED_PASSWORD", "magnet-qa-12345")

DEPARTMENT = {"slug": "core", "name": "Core"}

TENANTS: list[dict] = [
    {
        "slug": "qa-alpha",
        "name": "QA Alpha",
        "users": [
            {
                "email": "qa-alpha-admin@local.dev",
                "name": "QA Alpha Admin",
                "role_slug": "admin",
                "is_lead": True,
            },
            {
                "email": "qa-alpha-user@local.dev",
                "name": "QA Alpha User",
                "role_slug": "user",
            },
        ],
    },
    {
        "slug": "qa-beta",
        "name": "QA Beta",
        "users": [
            {
                "email": "qa-beta-admin@local.dev",
                "name": "QA Beta Admin",
                "role_slug": "admin",
                "is_lead": True,
            },
            {
                "email": "qa-beta-user@local.dev",
                "name": "QA Beta User",
                "role_slug": "user",
            },
        ],
    },
]


async def _get_or_create_tenant(
    session, *, slug: str, name: str
) -> tuple[Tenant, bool]:
    tenant = (
        await session.execute(select(Tenant).where(Tenant.slug == slug))
    ).scalar_one_or_none()
    if tenant is not None:
        return tenant, False
    tenant = Tenant(slug=slug, name=name, is_active=True)
    session.add(tenant)
    await session.flush()
    return tenant, True


async def _get_or_create_user(
    session, *, email: str, name: str, tenant_id: UUID
) -> tuple[User, bool]:
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


async def _ensure_role_assigned(
    session, *, tenant_id: UUID, user_id: UUID, role_id: UUID
) -> bool:
    existing = (
        await session.execute(
            select(UserRole).where(
                UserRole.user_id == user_id, UserRole.role_id == role_id
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        return False
    session.add(UserRole(tenant_id=tenant_id, user_id=user_id, role_id=role_id))
    await session.flush()
    return True


async def _ensure_department(
    session, *, tenant_id: UUID, slug: str, name: str
) -> Department:
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
    session,
    *,
    tenant_id: UUID,
    user_id: UUID,
    department_id: UUID,
    is_lead: bool = False,
) -> None:
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


async def _load_system_roles(session) -> dict[str, Role]:
    roles: dict[str, Role] = {}
    for slug in ("admin", "user", "viewer"):
        role = (
            await session.execute(
                select(Role).where(Role.slug == slug, Role.is_system == True)  # noqa: E712
            )
        ).scalar_one_or_none()
        if role is None:
            raise RuntimeError(f"System role {slug!r} missing — run migrations first.")
        roles[slug] = role
    return roles


async def main() -> None:
    print("Seeding QA test accounts…")
    print(f"  password = {DEFAULT_PASSWORD!r}")

    async with alchemy.get_session() as session:
        roles_by_slug = await _load_system_roles(session)

        for tenant_spec in TENANTS:
            tenant, created = await _get_or_create_tenant(
                session, slug=tenant_spec["slug"], name=tenant_spec["name"]
            )
            tag = "created" if created else "exists"
            print(f"\n  tenant  = {tenant.slug} ({tenant.id}) [{tag}]")

            await apply_session_rls(session, tenant_id=str(tenant.id))

            dept = await _ensure_department(
                session,
                tenant_id=tenant.id,
                slug=DEPARTMENT["slug"],
                name=DEPARTMENT["name"],
            )

            for user_spec in tenant_spec["users"]:
                user, was_created = await _get_or_create_user(
                    session,
                    email=user_spec["email"],
                    name=user_spec["name"],
                    tenant_id=tenant.id,
                )
                role = roles_by_slug[user_spec["role_slug"]]
                role_assigned = await _ensure_role_assigned(
                    session,
                    tenant_id=tenant.id,
                    user_id=user.id,
                    role_id=role.id,
                )
                await _ensure_membership(
                    session,
                    tenant_id=tenant.id,
                    user_id=user.id,
                    department_id=dept.id,
                    is_lead=user_spec.get("is_lead", False),
                )
                u_tag = "created" if was_created else "exists"
                lead_tag = " (lead)" if user_spec.get("is_lead") else ""
                role_tag = " (role assigned)" if role_assigned else ""
                print(
                    f"    user  = {user.email:32s} [{u_tag}] "
                    f"role={user_spec['role_slug']:6s} "
                    f"dept={dept.slug}{lead_tag}{role_tag}"
                )

        await session.commit()

    print("\nDone. Test accounts (all share the same password):")
    print(f"  password = {DEFAULT_PASSWORD!r}")
    for tenant_spec in TENANTS:
        print(f"  tenant {tenant_spec['slug']!r}:")
        for user_spec in tenant_spec["users"]:
            print(f"    {user_spec['email']:32s}  role={user_spec['role_slug']}")


if __name__ == "__main__":
    asyncio.run(main())
