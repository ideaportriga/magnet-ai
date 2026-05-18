"""Admin endpoints for user management (PR 5 of access-control plan).

List, get, update users + assign/revoke roles. Scoped to the caller's tenant.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Optional
from uuid import UUID

from litestar import Controller, Request, get, patch
from litestar.exceptions import (
    HTTPException,
    NotFoundException,
    PermissionDeniedException,
    ValidationException,
)
from litestar.status_codes import HTTP_409_CONFLICT
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from core.config.app import alchemy
from core.db.models.user.role import Role
from core.db.models.user.user import User
from core.db.models.user.user_role import UserRole
from core.domain.users.schemas import User as UserSchema
from core.domain.users.schemas import UserUpdate
from core.domain.users.service import UsersService
from guards.permissions import (
    Permission,
    load_role_permissions_cache,
    require_permission,
)
from middlewares.auth import Auth
from services.access_control import write_audit_log


class AdminUserResponse(UserSchema):
    """User payload for the admin UI — adds role slugs."""

    roles: list[str] = Field(default_factory=list)


def _serialize_admin_user(service: UsersService, user: User) -> AdminUserResponse:
    base = service.to_schema(user, schema_type=UserSchema).model_dump()
    base["roles"] = sorted({r.slug for r in (user.roles or [])})
    return AdminUserResponse.model_validate(base)


class UserRolesPatch(BaseModel):
    add: list[UUID] = Field(default_factory=list)
    remove: list[UUID] = Field(default_factory=list)


class UserRolesPatchResponse(BaseModel):
    added: list[UUID]
    removed: list[UUID]
    skipped_already_assigned: list[UUID] = Field(default_factory=list)
    skipped_not_assigned: list[UUID] = Field(default_factory=list)


def _require_auth(request: Request) -> Auth:
    auth: Auth | None = request.scope.get("auth")
    if auth is None:
        raise PermissionDeniedException("Authentication required.")
    return auth


def _require_tenant_id(auth: Auth) -> UUID:
    tenant_id = auth.tenant_id
    if not tenant_id:
        raise PermissionDeniedException("Tenant context required for user management.")
    return UUID(tenant_id)


def _get_actor_id(auth: Auth) -> Optional[UUID]:
    user = getattr(auth, "user", None)
    return getattr(user, "id", None) if user is not None else None


async def _load_target_user(session, user_id: UUID, tenant_id: UUID) -> User:
    user = (
        await session.execute(select(User).where(User.id == user_id))
    ).scalar_one_or_none()
    if user is None or user.tenant_id != tenant_id:
        raise NotFoundException("User not found")
    return user


class UsersController(Controller):
    path = "/users"
    tags = ["Admin / Users"]

    @get(
        summary="List users in the caller's tenant",
        guards=[require_permission(Permission.USERS_READ)],
    )
    async def list_users(self, request: Request) -> list[AdminUserResponse]:
        auth = _require_auth(request)
        tenant_id = _require_tenant_id(auth)
        async with alchemy.get_session() as session:
            service = UsersService(session=session)
            users = (
                (await session.execute(select(User).where(User.tenant_id == tenant_id)))
                .scalars()
                .all()
            )
            return [_serialize_admin_user(service, u) for u in users]

    @get(
        "/{id:uuid}",
        summary="Get user by ID (within caller's tenant)",
        guards=[require_permission(Permission.USERS_READ)],
    )
    async def get_user(self, request: Request, id: UUID) -> AdminUserResponse:
        auth = _require_auth(request)
        tenant_id = _require_tenant_id(auth)
        async with alchemy.get_session() as session:
            user = await _load_target_user(session, id, tenant_id)
            service = UsersService(session=session)
            return _serialize_admin_user(service, user)

    @patch(
        "/{id:uuid}",
        summary="Update user profile fields",
        guards=[require_permission(Permission.USERS_MANAGE)],
    )
    async def update_user(
        self, request: Request, id: UUID, data: UserUpdate
    ) -> UserSchema:
        auth = _require_auth(request)
        tenant_id = _require_tenant_id(auth)

        update_data = data.model_dump(exclude_unset=True)
        # `is_superuser` is platform-level, never settable from tenant admin UI.
        if "is_superuser" in update_data:
            raise PermissionDeniedException(
                "is_superuser cannot be set through tenant admin endpoints"
            )
        if "tenant_id" in update_data:
            raise PermissionDeniedException("tenant_id is not editable here")

        async with alchemy.get_session() as session:
            user = await _load_target_user(session, id, tenant_id)
            before = {k: getattr(user, k, None) for k in update_data}
            for key, value in update_data.items():
                setattr(user, key, value)
            service = UsersService(session=session)
            user = await service.update(user, auto_commit=False)

            await write_audit_log(
                session,
                tenant_id=tenant_id,
                actor_id=_get_actor_id(auth),
                action="user.update",
                target_type="user",
                target_id=user.id,
                payload={"before": before, "after": update_data},
            )
            await session.commit()
            return service.to_schema(user, schema_type=UserSchema)

    # ── Role assign / revoke ────────────────────────────────────────────

    @patch(
        "/{id:uuid}/roles",
        summary="Assign / revoke roles for a user",
        guards=[require_permission(Permission.USERS_MANAGE)],
    )
    async def update_roles(
        self, request: Request, id: UUID, data: UserRolesPatch
    ) -> UserRolesPatchResponse:
        auth = _require_auth(request)
        tenant_id = _require_tenant_id(auth)

        if not data.add and not data.remove:
            return UserRolesPatchResponse(added=[], removed=[])

        async with alchemy.get_session() as session:
            target = await _load_target_user(session, id, tenant_id)

            requested_role_ids = set(data.add) | set(data.remove)
            roles_by_id = await _load_roles(session, requested_role_ids)
            _validate_roles_in_tenant(roles_by_id, tenant_id)

            current_ids = {
                r[0]
                for r in (
                    await session.execute(
                        select(UserRole.role_id).where(UserRole.user_id == target.id)
                    )
                ).all()
            }

            add_ids = set(data.add) - current_ids
            already_assigned = set(data.add) & current_ids
            remove_ids = set(data.remove) & current_ids
            skipped_remove = set(data.remove) - current_ids

            # Last-admin lockout: if any of the to-be-removed roles is the
            # `admin` system role, ensure another active admin remains in the
            # tenant.
            admin_role_id = await _admin_role_id(session)
            if admin_role_id and admin_role_id in remove_ids:
                await _ensure_not_last_admin(
                    session,
                    tenant_id,
                    removing_user_id=target.id,
                    admin_role_id=admin_role_id,
                )

            # Apply removals first to avoid integrity hiccups.
            if remove_ids:
                await session.execute(
                    UserRole.__table__.delete().where(
                        (UserRole.user_id == target.id)
                        & (UserRole.role_id.in_(remove_ids))
                    )
                )

            for rid in add_ids:
                session.add(
                    UserRole(
                        user_id=target.id,
                        role_id=rid,
                        assigned_at=datetime.now(UTC),
                    )
                )

            for rid in add_ids:
                await write_audit_log(
                    session,
                    tenant_id=tenant_id,
                    actor_id=_get_actor_id(auth),
                    action="user.role.assign",
                    target_type="user",
                    target_id=target.id,
                    payload={"role_id": str(rid), "role_slug": roles_by_id[rid].slug},
                )
            for rid in remove_ids:
                await write_audit_log(
                    session,
                    tenant_id=tenant_id,
                    actor_id=_get_actor_id(auth),
                    action="user.role.revoke",
                    target_type="user",
                    target_id=target.id,
                    payload={"role_id": str(rid), "role_slug": roles_by_id[rid].slug},
                )

            await session.commit()
            # Role membership changed → refresh process-wide permission cache.
            await load_role_permissions_cache()

            return UserRolesPatchResponse(
                added=sorted(add_ids),
                removed=sorted(remove_ids),
                skipped_already_assigned=sorted(already_assigned),
                skipped_not_assigned=sorted(skipped_remove),
            )


async def _load_roles(session, role_ids: set[UUID]) -> dict[UUID, Role]:
    if not role_ids:
        return {}
    result = await session.execute(select(Role).where(Role.id.in_(role_ids)))
    roles = {r.id: r for r in result.scalars().all()}
    missing = role_ids - set(roles.keys())
    if missing:
        raise NotFoundException(
            f"Role(s) not found: {', '.join(sorted(str(x) for x in missing))}"
        )
    return roles


def _validate_roles_in_tenant(roles_by_id: dict[UUID, Role], tenant_id: UUID) -> None:
    for role in roles_by_id.values():
        # System roles (tenant_id IS NULL) are universally assignable.
        if role.tenant_id is None:
            continue
        if role.tenant_id != tenant_id:
            raise ValidationException(f"Role '{role.slug}' belongs to another tenant")


async def _admin_role_id(session) -> Optional[UUID]:
    row = (
        await session.execute(
            select(Role.id).where(
                Role.slug == "admin",
                Role.is_system == True,  # noqa: E712
            )
        )
    ).scalar_one_or_none()
    return row


async def _ensure_not_last_admin(
    session,
    tenant_id: UUID,
    *,
    removing_user_id: UUID,
    admin_role_id: UUID,
) -> None:
    """Refuse to remove `admin` from a user who is the tenant's only admin."""
    count_row = await session.execute(
        select(func.count(UserRole.user_id.distinct()))
        .join(User, User.id == UserRole.user_id)
        .where(
            UserRole.role_id == admin_role_id,
            User.tenant_id == tenant_id,
            User.is_active == True,  # noqa: E712
            User.id != removing_user_id,
        )
    )
    others = int(count_row.scalar() or 0)
    if others == 0:
        raise HTTPException(
            status_code=HTTP_409_CONFLICT,
            detail=(
                "Cannot remove 'admin' from the last active admin in this tenant. "
                "Promote another user to admin first."
            ),
        )
