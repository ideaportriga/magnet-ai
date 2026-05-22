"""Admin endpoints for tenant management (superuser only).

Tenant CRUD is cross-tenant by definition, so the standard
`require_permission(...)` gate isn't enough — every endpoint here also
checks `User.is_superuser`. The RLS superuser bypass (migration
2026-05-20) makes cross-tenant reads/writes actually work at the DB level.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from litestar import Controller, Request, get, patch, post
from litestar.exceptions import (
    NotFoundException,
    PermissionDeniedException,
    ValidationException,
)
from litestar.types import Guard
from pydantic import BaseModel
from sqlalchemy import func, select

from core.config.app import alchemy
from core.db.models.department.department import Department
from core.db.models.tenant.tenant import Tenant
from core.db.models.user.user import User
from core.domain.tenants.schemas import (
    TenantCreate,
    TenantResponse,
    TenantUpdate,
)
from middlewares.auth import Auth
from services.access_control import write_audit_log


def _require_superuser() -> Guard:
    def guard(connection, _handler):  # noqa: ANN001
        auth: Auth | None = connection.scope.get("auth")
        if auth is None:
            raise PermissionDeniedException("Authentication required.")
        user = getattr(auth, "user", None)
        if user is None or not getattr(user, "is_superuser", False):
            raise PermissionDeniedException(
                "Tenant management requires platform superuser."
            )

    return guard


def _require_auth(request: Request) -> Auth:
    auth: Auth | None = request.scope.get("auth")
    if auth is None:
        raise PermissionDeniedException("Authentication required.")
    return auth


def _actor_id(auth: Auth) -> Optional[UUID]:
    user = getattr(auth, "user", None)
    return getattr(user, "id", None) if user is not None else None


async def _load_tenant(session, tenant_id: UUID) -> Tenant:
    tenant = (
        await session.execute(select(Tenant).where(Tenant.id == tenant_id))
    ).scalar_one_or_none()
    if tenant is None:
        raise NotFoundException("Tenant not found")
    return tenant


async def _serialize(session, tenant: Tenant) -> TenantResponse:
    user_count = int(
        (
            await session.execute(
                select(func.count(User.id)).where(User.tenant_id == tenant.id)
            )
        ).scalar()
        or 0
    )
    dept_count = int(
        (
            await session.execute(
                select(func.count(Department.id)).where(
                    Department.tenant_id == tenant.id
                )
            )
        ).scalar()
        or 0
    )
    return TenantResponse(
        id=tenant.id,
        slug=tenant.slug,
        name=tenant.name,
        is_active=tenant.is_active,
        user_count=user_count,
        department_count=dept_count,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
    )


class TenantUserSummary(BaseModel):
    id: UUID
    email: Optional[str] = None
    name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False


class TenantsController(Controller):
    path = "/tenants"
    tags = ["Admin / Tenants"]
    guards = [_require_superuser()]

    @get(summary="List all tenants (superuser)")
    async def list_tenants(self, request: Request) -> list[TenantResponse]:
        _require_auth(request)
        async with alchemy.get_session() as session:
            tenants = (
                (await session.execute(select(Tenant).order_by(Tenant.slug)))
                .scalars()
                .all()
            )
            return [await _serialize(session, t) for t in tenants]

    @get("/{tenant_id:uuid}", summary="Get tenant by id (superuser)")
    async def get_tenant(self, request: Request, tenant_id: UUID) -> TenantResponse:
        _require_auth(request)
        async with alchemy.get_session() as session:
            tenant = await _load_tenant(session, tenant_id)
            return await _serialize(session, tenant)

    @post(summary="Create a tenant (superuser)")
    async def create_tenant(
        self, request: Request, data: TenantCreate
    ) -> TenantResponse:
        auth = _require_auth(request)
        async with alchemy.get_session() as session:
            existing = (
                await session.execute(select(Tenant).where(Tenant.slug == data.slug))
            ).scalar_one_or_none()
            if existing is not None:
                raise ValidationException(
                    f"Tenant with slug '{data.slug}' already exists"
                )
            tenant = Tenant(
                slug=data.slug,
                name=data.name,
                is_active=data.is_active,
            )
            session.add(tenant)
            await session.flush()

            await write_audit_log(
                session,
                tenant_id=tenant.id,
                actor_id=_actor_id(auth),
                action="tenant.create",
                target_type="tenant",
                target_id=tenant.id,
                payload={
                    "slug": tenant.slug,
                    "name": tenant.name,
                    "is_active": tenant.is_active,
                },
            )
            await session.commit()
            await session.refresh(tenant)
            return await _serialize(session, tenant)

    @patch("/{tenant_id:uuid}", summary="Update tenant (superuser)")
    async def update_tenant(
        self, request: Request, tenant_id: UUID, data: TenantUpdate
    ) -> TenantResponse:
        auth = _require_auth(request)
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise ValidationException("No fields to update")

        async with alchemy.get_session() as session:
            tenant = await _load_tenant(session, tenant_id)

            if "slug" in update_data and update_data["slug"] != tenant.slug:
                clash = (
                    await session.execute(
                        select(Tenant).where(
                            Tenant.slug == update_data["slug"],
                            Tenant.id != tenant.id,
                        )
                    )
                ).scalar_one_or_none()
                if clash is not None:
                    raise ValidationException(
                        f"Tenant with slug '{update_data['slug']}' already exists"
                    )

            before = {k: getattr(tenant, k) for k in update_data}
            for key, value in update_data.items():
                setattr(tenant, key, value)

            await write_audit_log(
                session,
                tenant_id=tenant.id,
                actor_id=_actor_id(auth),
                action="tenant.update",
                target_type="tenant",
                target_id=tenant.id,
                payload={"before": before, "after": update_data},
            )
            await session.commit()
            await session.refresh(tenant)
            return await _serialize(session, tenant)

    @get(
        "/{tenant_id:uuid}/users",
        summary="List users in a tenant (superuser)",
    )
    async def list_tenant_users(
        self, request: Request, tenant_id: UUID
    ) -> list[TenantUserSummary]:
        _require_auth(request)
        async with alchemy.get_session() as session:
            await _load_tenant(session, tenant_id)
            users = (
                (
                    await session.execute(
                        select(User)
                        .where(User.tenant_id == tenant_id)
                        .order_by(User.email)
                    )
                )
                .scalars()
                .all()
            )
            return [
                TenantUserSummary(
                    id=u.id,
                    email=u.email,
                    name=u.name,
                    is_active=u.is_active,
                    is_superuser=u.is_superuser,
                )
                for u in users
            ]
