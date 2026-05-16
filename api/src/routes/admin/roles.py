"""Admin endpoints for role management (PR 5 of access-control plan).

System roles: visible to all tenants, never editable (is_system=True,
tenant_id IS NULL). Seeded via migration; only a new migration can change
them.

Custom roles: tenant-scoped, editable by tenant admins. Their permission set
is capped by the creator's effective permissions (capability ceiling).
Deleting a role with active assignments returns 409 — the UI must reassign
or revoke first.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from litestar import Controller, Request, delete, get, patch, post, put
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
from core.db.models.user.permission import Permission as PermissionModel
from core.db.models.user.role import Role
from core.db.models.user.role_permission import RolePermission
from core.db.models.user.user_role import UserRole
from guards.permissions import (
    Permission,
    get_effective_permissions,
    load_role_permissions_cache,
    require_permission,
)
from middlewares.auth import Auth
from services.access_control import write_audit_log


class RoleResponse(BaseModel):
    id: UUID
    slug: str
    name: str
    description: Optional[str] = None
    is_system: bool
    tenant_id: Optional[UUID] = None
    permissions: list[str] = Field(default_factory=list)
    user_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class RoleCreateRequest(BaseModel):
    slug: str = Field(..., max_length=100)
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    permissions: list[str] = Field(default_factory=list)


class RoleUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None


class RolePermissionsReplace(BaseModel):
    permissions: list[str]


def _require_auth(request: Request) -> Auth:
    auth: Auth | None = request.scope.get("auth")
    if auth is None:
        raise PermissionDeniedException("Authentication required.")
    return auth


def _require_tenant_id(auth: Auth) -> UUID:
    tenant_id = auth.tenant_id
    if not tenant_id:
        raise PermissionDeniedException("Tenant context required for role management.")
    return UUID(tenant_id)


async def _validate_permission_codes(session, codes: list[str]) -> set[str]:
    """Return the subset of codes that exist in the catalog. Raise if any unknown."""
    if not codes:
        return set()
    unique = set(codes)
    result = await session.execute(
        select(PermissionModel.code).where(PermissionModel.code.in_(unique))
    )
    found = {row[0] for row in result.all()}
    missing = unique - found
    if missing:
        raise ValidationException(
            f"Unknown permission code(s): {', '.join(sorted(missing))}"
        )
    return unique


def _check_capability_ceiling(auth: Auth, requested: set[str]) -> None:
    """Creator can't grant permissions they don't themselves have."""
    user = getattr(auth, "user", None)
    if user is not None and getattr(user, "is_superuser", False):
        return  # platform superuser bypasses
    effective = get_effective_permissions(auth)
    not_allowed = requested - effective
    if not_allowed:
        raise PermissionDeniedException(
            "Cannot grant permissions you don't hold yourself: "
            + ", ".join(sorted(not_allowed))
        )


async def _serialize_role(session, role: Role) -> RoleResponse:
    grants = await session.execute(
        select(RolePermission.permission_code).where(RolePermission.role_id == role.id)
    )
    perm_codes = sorted(r[0] for r in grants.all())

    user_count_row = await session.execute(
        select(func.count()).select_from(UserRole).where(UserRole.role_id == role.id)
    )
    user_count = int(user_count_row.scalar() or 0)

    return RoleResponse(
        id=role.id,
        slug=role.slug,
        name=role.name,
        description=role.description,
        is_system=role.is_system,
        tenant_id=role.tenant_id,
        permissions=perm_codes,
        user_count=user_count,
        created_at=role.created_at,
        updated_at=role.updated_at,
    )


def _get_actor_id(auth: Auth) -> Optional[UUID]:
    user = getattr(auth, "user", None)
    if user is None:
        return None
    return user.id if hasattr(user, "id") else None


class RolesController(Controller):
    path = "/roles"
    tags = ["Admin / Roles"]

    # ── List / Get ──────────────────────────────────────────────────────

    @get(
        summary="List roles (system + own tenant custom)",
        guards=[require_permission(Permission.ROLES_READ)],
    )
    async def list_roles(self, request: Request) -> list[RoleResponse]:
        auth = _require_auth(request)
        tenant_id = _require_tenant_id(auth)

        async with alchemy.get_session() as session:
            stmt = (
                select(Role)
                .where((Role.tenant_id == tenant_id) | (Role.tenant_id.is_(None)))
                .order_by(Role.is_system.desc(), Role.slug)
            )
            roles = (await session.execute(stmt)).scalars().all()
            return [await _serialize_role(session, r) for r in roles]

    @get(
        "/{role_id:uuid}",
        summary="Get a role with permission codes and user count",
        guards=[require_permission(Permission.ROLES_READ)],
    )
    async def get_role(self, request: Request, role_id: UUID) -> RoleResponse:
        auth = _require_auth(request)
        tenant_id = _require_tenant_id(auth)

        async with alchemy.get_session() as session:
            role = (
                await session.execute(select(Role).where(Role.id == role_id))
            ).scalar_one_or_none()
            if role is None or (
                role.tenant_id is not None and role.tenant_id != tenant_id
            ):
                raise NotFoundException("Role not found")
            return await _serialize_role(session, role)

    # ── Create ──────────────────────────────────────────────────────────

    @post(
        summary="Create a custom tenant role",
        guards=[require_permission(Permission.ROLES_WRITE)],
    )
    async def create_role(
        self, request: Request, data: RoleCreateRequest
    ) -> RoleResponse:
        auth = _require_auth(request)
        tenant_id = _require_tenant_id(auth)

        # System slugs are reserved.
        if data.slug in {"admin", "user", "viewer"}:
            raise ValidationException(
                f"Slug '{data.slug}' is reserved for system roles"
            )

        async with alchemy.get_session() as session:
            permission_codes = await _validate_permission_codes(
                session, data.permissions
            )
            _check_capability_ceiling(auth, permission_codes)

            role = Role(
                slug=data.slug,
                name=data.name,
                description=data.description,
                is_system=False,
                tenant_id=tenant_id,
            )
            session.add(role)
            try:
                await session.flush()
            except Exception as exc:
                raise ValidationException(
                    f"Could not create role (slug/name collision?): {exc}"
                ) from exc

            for code in permission_codes:
                session.add(RolePermission(role_id=role.id, permission_code=code))

            await write_audit_log(
                session,
                tenant_id=tenant_id,
                actor_id=_get_actor_id(auth),
                action="role.create",
                target_type="role",
                target_id=role.id,
                payload={
                    "slug": data.slug,
                    "name": data.name,
                    "permissions": sorted(permission_codes),
                },
            )
            response = await _serialize_role(session, role)
            await session.commit()
            await load_role_permissions_cache()
            return response

    # ── Update metadata ─────────────────────────────────────────────────

    @patch(
        "/{role_id:uuid}",
        summary="Rename / re-describe a custom role",
        guards=[require_permission(Permission.ROLES_WRITE)],
    )
    async def update_role(
        self, request: Request, role_id: UUID, data: RoleUpdateRequest
    ) -> RoleResponse:
        auth = _require_auth(request)
        tenant_id = _require_tenant_id(auth)

        async with alchemy.get_session() as session:
            role = await _load_tenant_custom_role(session, role_id, tenant_id)

            before = {"name": role.name, "description": role.description}
            if data.name is not None:
                role.name = data.name
            if data.description is not None:
                role.description = data.description

            await write_audit_log(
                session,
                tenant_id=tenant_id,
                actor_id=_get_actor_id(auth),
                action="role.update",
                target_type="role",
                target_id=role.id,
                payload={
                    "before": before,
                    "after": data.model_dump(exclude_unset=True),
                },
            )
            await session.commit()
            return await _serialize_role(session, role)

    # ── Replace permission set ──────────────────────────────────────────

    @put(
        "/{role_id:uuid}/permissions",
        summary="Replace the permission set on a custom role",
        guards=[require_permission(Permission.ROLES_WRITE)],
    )
    async def replace_permissions(
        self,
        request: Request,
        role_id: UUID,
        data: RolePermissionsReplace,
    ) -> RoleResponse:
        auth = _require_auth(request)
        tenant_id = _require_tenant_id(auth)

        async with alchemy.get_session() as session:
            role = await _load_tenant_custom_role(session, role_id, tenant_id)

            new_codes = await _validate_permission_codes(session, data.permissions)
            _check_capability_ceiling(auth, new_codes)

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

            to_remove = existing_codes - new_codes
            to_add = new_codes - existing_codes

            if to_remove:
                await session.execute(
                    RolePermission.__table__.delete().where(
                        (RolePermission.role_id == role.id)
                        & (RolePermission.permission_code.in_(to_remove))
                    )
                )
            for code in to_add:
                session.add(RolePermission(role_id=role.id, permission_code=code))

            await write_audit_log(
                session,
                tenant_id=tenant_id,
                actor_id=_get_actor_id(auth),
                action="role.permissions.replace",
                target_type="role",
                target_id=role.id,
                payload={
                    "added": sorted(to_add),
                    "removed": sorted(to_remove),
                    "final": sorted(new_codes),
                },
            )
            response = await _serialize_role(session, role)
            await session.commit()
            await load_role_permissions_cache()
            return response

    # ── Delete ──────────────────────────────────────────────────────────

    @delete(
        "/{role_id:uuid}",
        summary="Delete a custom role (fails if assignments exist)",
        guards=[require_permission(Permission.ROLES_WRITE)],
    )
    async def delete_role(self, request: Request, role_id: UUID) -> None:
        auth = _require_auth(request)
        tenant_id = _require_tenant_id(auth)

        async with alchemy.get_session() as session:
            role = await _load_tenant_custom_role(session, role_id, tenant_id)

            count_row = await session.execute(
                select(func.count())
                .select_from(UserRole)
                .where(UserRole.role_id == role.id)
            )
            user_count = int(count_row.scalar() or 0)
            if user_count > 0:
                raise HTTPException(
                    status_code=HTTP_409_CONFLICT,
                    detail=(
                        f"Cannot delete role: {user_count} user(s) still assigned. "
                        "Reassign or revoke first."
                    ),
                )

            await write_audit_log(
                session,
                tenant_id=tenant_id,
                actor_id=_get_actor_id(auth),
                action="role.delete",
                target_type="role",
                target_id=role.id,
                payload={"slug": role.slug, "name": role.name},
            )

            await session.delete(role)
            await session.commit()
            await load_role_permissions_cache()


async def _load_tenant_custom_role(session, role_id: UUID, tenant_id: UUID) -> Role:
    role = (
        await session.execute(select(Role).where(Role.id == role_id))
    ).scalar_one_or_none()
    if role is None:
        raise NotFoundException("Role not found")
    if role.is_system:
        raise PermissionDeniedException("System roles cannot be modified")
    if role.tenant_id != tenant_id:
        raise NotFoundException("Role not found")
    return role
