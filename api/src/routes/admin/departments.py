"""Admin endpoints for department management.

Departments are tenant-scoped (PR 8 of access-control plan). Reads gate
on `read:users`, mutations gate on `manage:users` — same surface admins
use to assign roles. Each call inherits the caller's tenant from
`auth.tenant_id`; cross-tenant operations are not possible here.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from litestar import Controller, Request, delete, get, patch, post
from litestar.exceptions import (
    NotFoundException,
    PermissionDeniedException,
    ValidationException,
)
from sqlalchemy import func, select

from core.config.app import alchemy
from core.db.models.department.department import Department
from core.db.models.department.user_department import UserDepartment
from core.db.models.user.user import User
from core.domain.departments.schemas import (
    DepartmentCreate,
    DepartmentDetailResponse,
    DepartmentMember,
    DepartmentMemberAdd,
    DepartmentMemberUpdate,
    DepartmentResponse,
    DepartmentUpdate,
)
from guards.permissions import Permission, require_permission
from middlewares.auth import Auth
from services.access_control import write_audit_log


def _require_auth(request: Request) -> Auth:
    auth: Auth | None = request.scope.get("auth")
    if auth is None:
        raise PermissionDeniedException("Authentication required.")
    return auth


def _require_tenant_id(auth: Auth) -> UUID:
    tenant_id = auth.tenant_id
    if not tenant_id:
        raise PermissionDeniedException(
            "Tenant context required for department management."
        )
    return UUID(tenant_id)


def _actor_id(auth: Auth) -> Optional[UUID]:
    user = getattr(auth, "user", None)
    return getattr(user, "id", None) if user is not None else None


async def _load_department(session, dept_id: UUID, tenant_id: UUID) -> Department:
    dept = (
        await session.execute(select(Department).where(Department.id == dept_id))
    ).scalar_one_or_none()
    if dept is None or dept.tenant_id != tenant_id:
        raise NotFoundException("Department not found")
    return dept


async def _load_tenant_user(session, user_id: UUID, tenant_id: UUID) -> User:
    user = (
        await session.execute(select(User).where(User.id == user_id))
    ).scalar_one_or_none()
    if user is None or user.tenant_id != tenant_id:
        raise NotFoundException("User not in this tenant")
    return user


async def _member_count(session, dept_id: UUID) -> int:
    return int(
        (
            await session.execute(
                select(func.count(UserDepartment.id)).where(
                    UserDepartment.department_id == dept_id
                )
            )
        ).scalar()
        or 0
    )


def _to_summary(dept: Department, member_count: int) -> DepartmentResponse:
    return DepartmentResponse(
        id=dept.id,
        tenant_id=dept.tenant_id,
        slug=dept.slug,
        name=dept.name,
        parent_id=dept.parent_id,
        member_count=member_count,
        created_at=dept.created_at,
        updated_at=dept.updated_at,
    )


class DepartmentsController(Controller):
    path = "/departments"
    tags = ["Admin / Departments"]

    @get(
        summary="List departments in the caller's tenant",
        guards=[require_permission(Permission.USERS_READ)],
    )
    async def list_departments(self, request: Request) -> list[DepartmentResponse]:
        tenant_id = _require_tenant_id(_require_auth(request))
        async with alchemy.get_session() as session:
            depts = (
                (
                    await session.execute(
                        select(Department)
                        .where(Department.tenant_id == tenant_id)
                        .order_by(Department.slug)
                    )
                )
                .scalars()
                .all()
            )
            counts: dict[UUID, int] = {}
            if depts:
                rows = (
                    await session.execute(
                        select(
                            UserDepartment.department_id,
                            func.count(UserDepartment.id),
                        )
                        .where(UserDepartment.department_id.in_([d.id for d in depts]))
                        .group_by(UserDepartment.department_id)
                    )
                ).all()
                counts = {row[0]: int(row[1]) for row in rows}
            return [_to_summary(d, counts.get(d.id, 0)) for d in depts]

    @get(
        "/{dept_id:uuid}",
        summary="Get a department by id with its members",
        guards=[require_permission(Permission.USERS_READ)],
    )
    async def get_department(
        self, request: Request, dept_id: UUID
    ) -> DepartmentDetailResponse:
        tenant_id = _require_tenant_id(_require_auth(request))
        async with alchemy.get_session() as session:
            dept = await _load_department(session, dept_id, tenant_id)
            members_rows = (
                await session.execute(
                    select(UserDepartment, User)
                    .join(User, User.id == UserDepartment.user_id)
                    .where(UserDepartment.department_id == dept.id)
                    .order_by(User.email)
                )
            ).all()
            members = [
                DepartmentMember(
                    user_id=u.id,
                    email=u.email,
                    name=u.name,
                    is_lead=m.is_lead,
                )
                for (m, u) in members_rows
            ]
            return DepartmentDetailResponse(
                id=dept.id,
                tenant_id=dept.tenant_id,
                slug=dept.slug,
                name=dept.name,
                parent_id=dept.parent_id,
                member_count=len(members),
                created_at=dept.created_at,
                updated_at=dept.updated_at,
                members=members,
            )

    @post(
        summary="Create a department in the caller's tenant",
        guards=[require_permission(Permission.USERS_MANAGE)],
    )
    async def create_department(
        self, request: Request, data: DepartmentCreate
    ) -> DepartmentResponse:
        auth = _require_auth(request)
        tenant_id = _require_tenant_id(auth)
        async with alchemy.get_session() as session:
            if data.parent_id is not None:
                parent = await _load_department(session, data.parent_id, tenant_id)
                if parent is None:
                    raise ValidationException("parent_id does not belong to tenant")

            clash = (
                await session.execute(
                    select(Department).where(
                        Department.tenant_id == tenant_id,
                        Department.slug == data.slug,
                    )
                )
            ).scalar_one_or_none()
            if clash is not None:
                raise ValidationException(
                    f"Department slug '{data.slug}' already used in tenant"
                )

            dept = Department(
                tenant_id=tenant_id,
                slug=data.slug,
                name=data.name,
                parent_id=data.parent_id,
            )
            session.add(dept)
            await session.flush()

            await write_audit_log(
                session,
                tenant_id=tenant_id,
                actor_id=_actor_id(auth),
                action="department.create",
                target_type="department",
                target_id=dept.id,
                payload={"slug": dept.slug, "name": dept.name},
            )
            await session.commit()
            await session.refresh(dept)
            return _to_summary(dept, 0)

    @patch(
        "/{dept_id:uuid}",
        summary="Update a department",
        guards=[require_permission(Permission.USERS_MANAGE)],
    )
    async def update_department(
        self, request: Request, dept_id: UUID, data: DepartmentUpdate
    ) -> DepartmentResponse:
        auth = _require_auth(request)
        tenant_id = _require_tenant_id(auth)
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise ValidationException("No fields to update")

        async with alchemy.get_session() as session:
            dept = await _load_department(session, dept_id, tenant_id)

            if "slug" in update_data and update_data["slug"] != dept.slug:
                clash = (
                    await session.execute(
                        select(Department).where(
                            Department.tenant_id == tenant_id,
                            Department.slug == update_data["slug"],
                            Department.id != dept.id,
                        )
                    )
                ).scalar_one_or_none()
                if clash is not None:
                    raise ValidationException(
                        f"Department slug '{update_data['slug']}' already used"
                    )

            if "parent_id" in update_data:
                parent_id = update_data["parent_id"]
                if parent_id is not None:
                    if parent_id == dept.id:
                        raise ValidationException("Department cannot be its own parent")
                    await _load_department(session, parent_id, tenant_id)

            before = {k: getattr(dept, k) for k in update_data}
            for key, value in update_data.items():
                setattr(dept, key, value)

            await write_audit_log(
                session,
                tenant_id=tenant_id,
                actor_id=_actor_id(auth),
                action="department.update",
                target_type="department",
                target_id=dept.id,
                payload={"before": before, "after": update_data},
            )
            await session.commit()
            await session.refresh(dept)
            count = await _member_count(session, dept.id)
            return _to_summary(dept, count)

    @delete(
        "/{dept_id:uuid}",
        summary="Delete a department (and its memberships)",
        guards=[require_permission(Permission.USERS_MANAGE)],
    )
    async def delete_department(self, request: Request, dept_id: UUID) -> None:
        auth = _require_auth(request)
        tenant_id = _require_tenant_id(auth)
        async with alchemy.get_session() as session:
            dept = await _load_department(session, dept_id, tenant_id)
            await session.delete(dept)
            await write_audit_log(
                session,
                tenant_id=tenant_id,
                actor_id=_actor_id(auth),
                action="department.delete",
                target_type="department",
                target_id=dept_id,
                payload={"slug": dept.slug, "name": dept.name},
            )
            await session.commit()

    @post(
        "/{dept_id:uuid}/members",
        summary="Add a user to the department",
        guards=[require_permission(Permission.USERS_MANAGE)],
    )
    async def add_member(
        self, request: Request, dept_id: UUID, data: DepartmentMemberAdd
    ) -> DepartmentMember:
        auth = _require_auth(request)
        tenant_id = _require_tenant_id(auth)
        async with alchemy.get_session() as session:
            dept = await _load_department(session, dept_id, tenant_id)
            user = await _load_tenant_user(session, data.user_id, tenant_id)

            existing = (
                await session.execute(
                    select(UserDepartment).where(
                        UserDepartment.user_id == user.id,
                        UserDepartment.department_id == dept.id,
                    )
                )
            ).scalar_one_or_none()
            if existing is not None:
                if existing.is_lead != data.is_lead:
                    existing.is_lead = data.is_lead
                    await session.commit()
                return DepartmentMember(
                    user_id=user.id,
                    email=user.email,
                    name=user.name,
                    is_lead=existing.is_lead,
                )

            membership = UserDepartment(
                tenant_id=tenant_id,
                user_id=user.id,
                department_id=dept.id,
                is_lead=data.is_lead,
            )
            session.add(membership)
            await write_audit_log(
                session,
                tenant_id=tenant_id,
                actor_id=_actor_id(auth),
                action="department.member.add",
                target_type="department",
                target_id=dept.id,
                payload={"user_id": str(user.id), "is_lead": data.is_lead},
            )
            await session.commit()
            return DepartmentMember(
                user_id=user.id,
                email=user.email,
                name=user.name,
                is_lead=data.is_lead,
            )

    @patch(
        "/{dept_id:uuid}/members/{member_id:uuid}",
        summary="Toggle the is_lead flag for a department member",
        guards=[require_permission(Permission.USERS_MANAGE)],
    )
    async def update_member(
        self,
        request: Request,
        dept_id: UUID,
        member_id: UUID,
        data: DepartmentMemberUpdate,
    ) -> DepartmentMember:
        auth = _require_auth(request)
        tenant_id = _require_tenant_id(auth)
        async with alchemy.get_session() as session:
            dept = await _load_department(session, dept_id, tenant_id)
            user = await _load_tenant_user(session, member_id, tenant_id)
            membership = (
                await session.execute(
                    select(UserDepartment).where(
                        UserDepartment.user_id == user.id,
                        UserDepartment.department_id == dept.id,
                    )
                )
            ).scalar_one_or_none()
            if membership is None:
                raise NotFoundException("User is not a member of this department")
            membership.is_lead = data.is_lead
            await write_audit_log(
                session,
                tenant_id=tenant_id,
                actor_id=_actor_id(auth),
                action="department.member.update",
                target_type="department",
                target_id=dept.id,
                payload={"user_id": str(user.id), "is_lead": data.is_lead},
            )
            await session.commit()
            return DepartmentMember(
                user_id=user.id,
                email=user.email,
                name=user.name,
                is_lead=membership.is_lead,
            )

    @delete(
        "/{dept_id:uuid}/members/{member_id:uuid}",
        summary="Remove a user from the department",
        guards=[require_permission(Permission.USERS_MANAGE)],
    )
    async def remove_member(
        self, request: Request, dept_id: UUID, member_id: UUID
    ) -> None:
        auth = _require_auth(request)
        tenant_id = _require_tenant_id(auth)
        async with alchemy.get_session() as session:
            dept = await _load_department(session, dept_id, tenant_id)
            membership = (
                await session.execute(
                    select(UserDepartment).where(
                        UserDepartment.user_id == member_id,
                        UserDepartment.department_id == dept.id,
                    )
                )
            ).scalar_one_or_none()
            if membership is None:
                raise NotFoundException("User is not a member of this department")
            await session.delete(membership)
            await write_audit_log(
                session,
                tenant_id=tenant_id,
                actor_id=_actor_id(auth),
                action="department.member.remove",
                target_type="department",
                target_id=dept.id,
                payload={"user_id": str(member_id)},
            )
            await session.commit()
