"""Idempotent superuser bootstrap for fresh deployments and dev sessions.

Used in two places:
- ``scripts/bootstrap_superuser.py`` for explicit CLI invocation (CI, prod
  bootstrap, `npm run bootstrap:superuser`).
- ``core/server/plugins/startup.py`` when ``AUTO_CREATE_SUPERUSER=true`` —
  dev convenience so a fresh ``npm run dev`` lands you in a usable app
  without a separate manual step.

Both call the same function so behaviour is identical regardless of entry
point.
"""

from __future__ import annotations

from dataclasses import dataclass
from logging import getLogger
from typing import Any
from uuid import UUID

from sqlalchemy import select

from core.db.models.tenant.tenant import Tenant
from core.db.models.user.role import Role
from core.db.models.user.user import User
from core.db.models.user.user_role import UserRole
from core.domain.users.service import UsersService
from guards.role import SUPERUSER_ROLE_SLUG
from services.users.password import hash_password_async

logger = getLogger(__name__)


@dataclass
class BootstrapResult:
    user_id: UUID
    email: str
    created: bool
    """True if the user did not exist and was just inserted."""
    updated: bool
    """True if an existing user was promoted (is_superuser/is_active/is_verified
    flipped) or had the admin role assigned."""
    role_assigned: bool
    """True if the admin role was assigned in this run."""


async def bootstrap_superuser(
    session: Any,
    *,
    email: str,
    password: str,
    name: str | None = None,
    reset_password: bool = False,
) -> BootstrapResult:
    """Ensure that a superuser with ``email`` exists and is fully set up.

    Idempotent — safe to run on every startup or in a deploy hook.

    Behaviour:
    - If no user exists: create with hashed password, ``is_superuser=True``,
      ``is_active=True``, ``is_verified=True``, and assign the ``admin`` role.
    - If a user exists: ensure the three flags are True. Reassign the admin
      role if missing. Replace the password ONLY when ``reset_password=True``
      — otherwise an existing user keeps their password to avoid surprise
      lockouts when this is wired into startup.

    Caller is responsible for ``session.commit()``.
    """
    service = UsersService(session=session)
    user = await service.get_one_or_none(email=email)

    created = False
    updated = False

    if user is None:
        # Assign the default tenant — required NOT NULL since PR 4 of the
        # access-control plan. A bootstrap superuser belongs to the platform
        # tenant by convention (`slug='default'`).
        default_tenant_id = (
            await session.execute(select(Tenant.id).where(Tenant.slug == "default"))
        ).scalar_one_or_none()
        if default_tenant_id is None:
            raise RuntimeError(
                "bootstrap_superuser: default tenant not seeded — run migrations first"
            )
        user = User(
            email=email,
            name=name,
            hashed_password=await hash_password_async(password),
            is_active=True,
            is_superuser=True,
            is_verified=True,
            tenant_id=default_tenant_id,
        )
        user = await service.create(user, auto_commit=False)
        created = True
        logger.info("bootstrap_superuser created user email=%s", email)
    else:
        if not user.is_superuser:
            user.is_superuser = True
            updated = True
        if not user.is_active:
            user.is_active = True
            updated = True
        if not user.is_verified:
            user.is_verified = True
            updated = True
        if name and user.name != name:
            user.name = name
            updated = True
        if reset_password:
            user.hashed_password = await hash_password_async(password)
            updated = True
        if updated:
            await service.update(user, auto_commit=False)
            logger.info("bootstrap_superuser promoted existing user email=%s", email)
        else:
            logger.info(
                "bootstrap_superuser no-op — user already a superuser email=%s",
                email,
            )

    role_assigned = await _ensure_admin_role(session, user.id)
    if role_assigned:
        updated = True

    return BootstrapResult(
        user_id=user.id,
        email=user.email,
        created=created,
        updated=updated,
        role_assigned=role_assigned,
    )


async def _ensure_admin_role(session: Any, user_id: UUID) -> bool:
    """Assign the admin role to ``user_id`` if not already assigned.

    Returns True if the role was newly assigned in this call.
    """
    admin_role_stmt = select(Role).where(Role.slug == SUPERUSER_ROLE_SLUG)
    admin_role = (await session.execute(admin_role_stmt)).scalar_one_or_none()
    if admin_role is None:
        logger.warning(
            "Admin role '%s' not found — RBAC migration probably has not run yet",
            SUPERUSER_ROLE_SLUG,
        )
        return False

    existing_stmt = select(UserRole).where(
        UserRole.user_id == user_id,
        UserRole.role_id == admin_role.id,
    )
    existing = (await session.execute(existing_stmt)).scalar_one_or_none()
    if existing is not None:
        return False

    session.add(UserRole(user_id=user_id, role_id=admin_role.id))
    return True
