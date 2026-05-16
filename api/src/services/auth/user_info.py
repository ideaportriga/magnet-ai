"""
Helper to build user info response from internal User object.

Used by /api/v2/auth/me to avoid code duplication.
"""

from __future__ import annotations

from logging import getLogger

from core.db.models.user.user import User
from guards.permissions import get_effective_permissions
from middlewares.auth import Auth

logger = getLogger(__name__)


async def build_user_info(user: User, auth: Auth) -> dict:
    """Build a user info dict from a User object and Auth context."""
    role_slugs: list[str] = []
    roles_detailed: list[dict] = []
    try:
        for r in user.roles or []:
            role_slugs.append(r.slug)
            roles_detailed.append(
                {
                    "id": str(r.id),
                    "slug": r.slug,
                    "name": r.name,
                    "is_system": bool(getattr(r, "is_system", True)),
                }
            )
    except Exception:
        logger.warning("Failed to load roles for user %s", user.id, exc_info=True)

    oauth_accounts, departments, groups = await _load_related_user_info(user)

    permissions = sorted(get_effective_permissions(auth))

    tenant_block: dict | None = None
    tenant = getattr(user, "tenant", None)
    if tenant is not None:
        tenant_block = {
            "id": str(tenant.id),
            "slug": tenant.slug,
            "name": tenant.name,
        }

    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "avatar_url": user.avatar_url,
        "is_verified": user.is_verified,
        "is_superuser": user.is_superuser,
        "is_two_factor_enabled": user.is_two_factor_enabled,
        "roles": role_slugs,
        "roles_detailed": roles_detailed,
        "permissions": permissions,
        "tenant": tenant_block,
        "departments": departments,
        "groups": groups,
        "auth_method": auth.type,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "oauth_accounts": oauth_accounts,
    }


async def _load_related_user_info(
    user: User,
) -> tuple[list[dict], list[dict], list[dict]]:
    """Load /me auxiliary lists from one tenant-scoped session."""
    try:
        from core.config.app import alchemy
        from core.db.models.department import Department, UserDepartment
        from core.db.models.user.group import Group
        from core.db.models.user.user_group import UserGroup
        from core.db.models.user.user_oauth_account import UserOAuthAccount
        from sqlalchemy import select

        async with alchemy.get_session() as session:
            oauth_rows = (
                (
                    await session.execute(
                        select(UserOAuthAccount).where(
                            UserOAuthAccount.user_id == user.id
                        )
                    )
                )
                .scalars()
                .all()
            )

            department_rows = (
                await session.execute(
                    select(Department, UserDepartment.is_lead)
                    .join(UserDepartment, UserDepartment.department_id == Department.id)
                    .where(
                        UserDepartment.user_id == user.id,
                        UserDepartment.tenant_id == user.tenant_id,
                    )
                )
            ).all()

            group_rows = (
                await session.execute(
                    select(Group, UserGroup.role_in_group)
                    .join(UserGroup, UserGroup.group_id == Group.id)
                    .where(
                        UserGroup.user_id == user.id,
                        UserGroup.tenant_id == user.tenant_id,
                    )
                )
            ).all()

        oauth_accounts = [
            {"provider": oa.oauth_name, "email": oa.account_email} for oa in oauth_rows
        ]
        departments = [
            {
                "id": str(dept.id),
                "slug": dept.slug,
                "name": dept.name,
                "is_lead": bool(is_lead),
            }
            for dept, is_lead in department_rows
        ]
        groups = [
            {
                "id": str(group.id),
                "slug": group.slug,
                "name": group.name,
                "role": role_in_group,
            }
            for group, role_in_group in group_rows
        ]
        return oauth_accounts, departments, groups
    except Exception:
        logger.warning(
            "Failed to load related /me info for user %s", user.id, exc_info=True
        )
        return [], [], []
