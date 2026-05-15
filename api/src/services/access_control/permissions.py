"""
PermissionService — single-record authorization check (PR 8).

Implements the 11-step algorithm from the access-control plan. Used by
controllers when answering "may this principal do X to this record?"
For list endpoints there's a separate SQL builder in this module
(`record_visibility_filter`) so we never N+1 through `can()`.

Public API:

    await PermissionService.can(
        session,
        auth=auth,
        action="edit",
        resource_type="agents",
        resource=agent,
    ) -> bool

    await PermissionService.compute_record_permissions(
        session, auth=auth, resource_type="agents", resource=agent
    ) -> {"view": True, "edit": False, "delete": False, "share": False}

Action mapping to global permission codes is in `_ACTION_TO_CAPABILITY`. Add
new resource types there as the rollout extends in PR 10+.
"""

from __future__ import annotations

from typing import Any, Iterable, Literal, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models.access_grant import ResourceAccessGrant
from core.db.models.access_grant.resource_access_grant import (
    ACCESS_ADMIN,
    ACCESS_READ,
    ACCESS_WRITE,
    PRINCIPAL_DEPARTMENT,
    PRINCIPAL_GROUP,
    PRINCIPAL_USER,
)
from core.db.models.department.user_department import UserDepartment
from core.db.models.user.user_group import UserGroup
from guards.permissions import Permission, get_effective_permissions
from middlewares.auth import Auth

Action = Literal["view", "create", "edit", "delete", "share", "execute"]
ALL_ACTIONS: tuple[Action, ...] = ("view", "edit", "delete", "share")

VISIBILITY_PRIVATE = "private"
VISIBILITY_DEPARTMENT = "department"
VISIBILITY_TENANT = "tenant"


# Maps (resource_type, action) → required global permission code.
# Per the plan's capability ceiling: grants and visibility only narrow access;
# without the right global capability the answer is always False.
#
# Build the table dictionary-driven from the catalog: every resource type
# that has corresponding permission codes is registered here automatically.
# Adding a new resource to the rollout is then a matter of declaring its
# enum values — no need to remember to also update this table.

_ACTION_VERB_MAP: dict[Action, str] = {
    "view": "read",
    "edit": "write",
    "create": "write",
    "delete": "delete",
    "share": "share",
    "execute": "execute",
}


def _build_action_to_capability() -> dict[tuple[str, "Action"], Permission]:
    codes = {p.value for p in Permission}
    table: dict[tuple[str, Action], Permission] = {}
    for resource_type in sorted({p.value.split(":", 1)[1] for p in Permission}):
        for action, verb in _ACTION_VERB_MAP.items():
            code = f"{verb}:{resource_type}"
            if code in codes:
                table[(resource_type, action)] = Permission(code)
    return table


_ACTION_TO_CAPABILITY: dict[tuple[str, Action], Permission] = (
    _build_action_to_capability()
)


_ADMIN_ROLE_SLUG = "admin"


class PermissionService:
    """Stateless. All methods take the session + auth + record explicitly."""

    @staticmethod
    async def can(
        session: AsyncSession,
        *,
        auth: Auth | None,
        action: Action,
        resource_type: str,
        resource: Any | None = None,
    ) -> bool:
        # 1. Authenticated?
        if auth is None:
            return False
        user = getattr(auth, "user", None)

        # 2. Platform superuser bypass.
        if user is not None and getattr(user, "is_superuser", False):
            return True

        principal_tenant_id = _principal_tenant_id(auth)

        # 3. Cross-tenant short-circuit (controllers should already return 404).
        if resource is not None and principal_tenant_id is not None:
            resource_tenant_id = getattr(resource, "tenant_id", None)
            if resource_tenant_id is not None and str(resource_tenant_id) != str(
                principal_tenant_id
            ):
                return False

        # 4. Global capability ceiling.
        required = _ACTION_TO_CAPABILITY.get((resource_type, action))
        if required is None:
            return False
        effective = get_effective_permissions(auth)
        if required.value not in effective:
            return False

        # 5. Create: controller forces tenant/owner from auth, so capability
        #    + tenant context are enough.
        if action == "create":
            return True

        # No resource means we can only answer aggregate questions (which
        # `compute_record_permissions` doesn't ask).
        if resource is None:
            return False

        # 6. Tenant admin in own tenant.
        if _is_tenant_admin(user):
            return True

        owner_id = getattr(resource, "owner_id", None)
        visibility = (
            getattr(resource, "visibility", VISIBILITY_TENANT) or VISIBILITY_TENANT
        )
        department_id = getattr(resource, "department_id", None)
        user_id = _principal_user_id(auth)

        # 7. Owner can do anything their capability allows.
        if (
            user_id is not None
            and owner_id is not None
            and str(owner_id) == str(user_id)
        ):
            return True

        # 8. visibility='tenant' grants view to everyone with read capability.
        if visibility == VISIBILITY_TENANT and action == "view":
            return True

        # 9. visibility='department' — members can view; leads can edit/delete/share.
        if visibility == VISIBILITY_DEPARTMENT and department_id is not None:
            membership = await _load_department_membership(
                session, user_id=user_id, department_id=department_id
            )
            if membership is not None:
                if action == "view":
                    return True
                # edit/delete/share need lead or explicit grant.
                if membership.is_lead:
                    return True

        # 10. Explicit grants — user, then group, then department.
        grant_level = await _highest_grant_level(
            session,
            tenant_id=principal_tenant_id,
            resource_type=resource_type,
            resource_id=getattr(resource, "id"),
            user_id=user_id,
        )
        if grant_level is not None and _grant_satisfies(grant_level, action):
            return True

        # 11. Otherwise, no.
        return False

    @staticmethod
    async def compute_record_permissions(
        session: AsyncSession,
        *,
        auth: Auth | None,
        resource_type: str,
        resource: Any,
    ) -> dict[str, bool]:
        """Return the `_permissions` block attached to API responses."""
        results: dict[str, bool] = {}
        for action in ALL_ACTIONS:
            results[action] = await PermissionService.can(
                session,
                auth=auth,
                action=action,
                resource_type=resource_type,
                resource=resource,
            )
        return results


# ---------------------------------------------------------------------------
# SQL filter for list endpoints
# ---------------------------------------------------------------------------


async def record_visibility_filter(
    session: AsyncSession,
    *,
    auth: Auth,
    model,
    resource_type: str,
):
    """Return a SQLAlchemy column expression for the WHERE clause of a list.

    Combines:
      - tenant boundary (already enforced by RLS, kept here for clarity)
      - owner_id == user_id
      - visibility='tenant' (read capability already enforced by the guard)
      - visibility='department' with membership
      - explicit grants where principal matches user / group / department

    Tenant admins short-circuit to `True` (see all rows in tenant).
    """
    from sqlalchemy import and_, or_, true

    user = getattr(auth, "user", None)
    if user is not None and getattr(user, "is_superuser", False):
        return true()
    if _is_tenant_admin(user):
        return true()

    user_id = _principal_user_id(auth)
    tenant_id = _principal_tenant_id(auth)

    clauses = []

    # Tenant boundary (defensive — RLS already enforces).
    if tenant_id is not None and hasattr(model, "tenant_id"):
        clauses.append(model.tenant_id == _as_uuid(tenant_id))

    visibility_or_owner = []

    if hasattr(model, "owner_id") and user_id is not None:
        visibility_or_owner.append(model.owner_id == _as_uuid(user_id))

    if hasattr(model, "visibility"):
        visibility_or_owner.append(model.visibility == VISIBILITY_TENANT)

        # visibility='department' AND user is in that dept.
        if user_id is not None and hasattr(model, "department_id"):
            dept_ids = await _user_department_ids(session, user_id=user_id)
            if dept_ids:
                visibility_or_owner.append(
                    and_(
                        model.visibility == VISIBILITY_DEPARTMENT,
                        model.department_id.in_(dept_ids),
                    )
                )

    # Explicit grants by user / group / department.
    grant_resource_ids = await _granted_resource_ids(
        session,
        tenant_id=tenant_id,
        resource_type=resource_type,
        user_id=user_id,
    )
    if grant_resource_ids:
        visibility_or_owner.append(model.id.in_(grant_resource_ids))

    if visibility_or_owner:
        clauses.append(or_(*visibility_or_owner))
    else:
        # No visibility / ownership criteria available → deny.
        return _false_filter()

    return and_(*clauses)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _principal_user_id(auth: Auth) -> Optional[str]:
    user = getattr(auth, "user", None)
    if user is not None and getattr(user, "id", None) is not None:
        return str(user.id)
    return None


def _principal_tenant_id(auth: Auth) -> Optional[str]:
    return auth.tenant_id


def _is_tenant_admin(user: Any | None) -> bool:
    if user is None:
        return False
    roles = getattr(user, "roles", None) or []
    for role in roles:
        if getattr(role, "slug", None) == _ADMIN_ROLE_SLUG and getattr(
            role, "is_system", True
        ):
            return True
    return False


def _grant_satisfies(level: str, action: Action) -> bool:
    # Capability ceiling has already been checked at step 4.
    if level == ACCESS_ADMIN:
        return action in {"view", "edit", "delete", "share"}
    if level == ACCESS_WRITE:
        return action in {"view", "edit"}
    if level == ACCESS_READ:
        return action == "view"
    return False


async def _load_department_membership(
    session: AsyncSession,
    *,
    user_id: Optional[str],
    department_id: UUID | str,
) -> UserDepartment | None:
    if user_id is None:
        return None
    result = await session.execute(
        select(UserDepartment).where(
            UserDepartment.user_id == _as_uuid(user_id),
            UserDepartment.department_id == _as_uuid(department_id),
        )
    )
    return result.scalar_one_or_none()


async def _highest_grant_level(
    session: AsyncSession,
    *,
    tenant_id: Optional[str],
    resource_type: str,
    resource_id: UUID | str,
    user_id: Optional[str],
) -> Optional[str]:
    """Look up the strongest grant for this (resource, principal)."""
    if tenant_id is None or user_id is None:
        return None

    # User-direct grants.
    principals: list[tuple[str, UUID]] = [(PRINCIPAL_USER, _as_uuid(user_id))]

    # Group grants — fetch user's groups.
    group_rows = await session.execute(
        select(UserGroup.group_id).where(UserGroup.user_id == _as_uuid(user_id))
    )
    for (group_id,) in group_rows.all():
        principals.append((PRINCIPAL_GROUP, group_id))

    # Department grants — fetch user's departments.
    dept_rows = await session.execute(
        select(UserDepartment.department_id).where(
            UserDepartment.user_id == _as_uuid(user_id)
        )
    )
    for (dept_id,) in dept_rows.all():
        principals.append((PRINCIPAL_DEPARTMENT, dept_id))

    # Filter into one query.
    levels = await session.execute(
        select(ResourceAccessGrant.access_level).where(
            ResourceAccessGrant.tenant_id == _as_uuid(tenant_id),
            ResourceAccessGrant.resource_type == resource_type,
            ResourceAccessGrant.resource_id == _as_uuid(resource_id),
            _principal_disjunction(principals),
        )
    )
    found = [row[0] for row in levels.all()]
    if not found:
        return None

    # Pick highest: admin > write > read.
    order = {ACCESS_ADMIN: 3, ACCESS_WRITE: 2, ACCESS_READ: 1}
    return max(found, key=lambda lv: order.get(lv, 0))


def _principal_disjunction(principals: Iterable[tuple[str, UUID]]):
    from sqlalchemy import and_, or_

    clauses = []
    for ptype, pid in principals:
        clauses.append(
            and_(
                ResourceAccessGrant.principal_type == ptype,
                ResourceAccessGrant.principal_id == pid,
            )
        )
    if not clauses:
        return _false_filter()
    return or_(*clauses)


async def _user_department_ids(session: AsyncSession, *, user_id: str) -> list[UUID]:
    rows = await session.execute(
        select(UserDepartment.department_id).where(
            UserDepartment.user_id == _as_uuid(user_id)
        )
    )
    return [r[0] for r in rows.all()]


async def _granted_resource_ids(
    session: AsyncSession,
    *,
    tenant_id: Optional[str],
    resource_type: str,
    user_id: Optional[str],
) -> list[UUID]:
    if tenant_id is None or user_id is None:
        return []

    # Build the principal disjunction across user / groups / departments.
    principals: list[tuple[str, UUID]] = [(PRINCIPAL_USER, _as_uuid(user_id))]
    group_rows = await session.execute(
        select(UserGroup.group_id).where(UserGroup.user_id == _as_uuid(user_id))
    )
    for (gid,) in group_rows.all():
        principals.append((PRINCIPAL_GROUP, gid))
    dept_rows = await session.execute(
        select(UserDepartment.department_id).where(
            UserDepartment.user_id == _as_uuid(user_id)
        )
    )
    for (did,) in dept_rows.all():
        principals.append((PRINCIPAL_DEPARTMENT, did))

    result = await session.execute(
        select(ResourceAccessGrant.resource_id).where(
            ResourceAccessGrant.tenant_id == _as_uuid(tenant_id),
            ResourceAccessGrant.resource_type == resource_type,
            _principal_disjunction(principals),
        )
    )
    return [r[0] for r in result.all()]


def _as_uuid(value: UUID | str) -> UUID:
    return value if isinstance(value, UUID) else UUID(str(value))


def _false_filter():
    from sqlalchemy import false

    return false()
