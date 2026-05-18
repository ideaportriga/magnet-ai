"""Shared record-level helpers for tenant-scoped resource controllers.

PR 10 rollout — each new resource (collections, prompts, ai_apps, ...)
needs the same five things on top of its existing CRUD:

  1. force `tenant_id` and `owner_id` from auth context on create
  2. record-level `view` check on get/update/delete (404 vs 403)
  3. `_permissions` block attached to every response payload
  4. record-level visibility filter on list endpoints
  5. consistent error semantics (404 to not disclose existence)

This module centralises the patterns. Each resource controller imports the
two helpers below; ~50% of the per-entity boilerplate goes away.
"""

from __future__ import annotations

from logging import getLogger
from typing import Any

from litestar import Request
from litestar.exceptions import NotFoundException, PermissionDeniedException

from middlewares.auth import Auth
from services.access_control.permissions import (
    PermissionService,
    record_visibility_filter,
)

logger = getLogger(__name__)


IDENTITY_FIELDS = ("tenant_id", "owner_id")


def force_create_fields(
    payload: dict[str, Any],
    *,
    request: Request,
) -> dict[str, Any]:
    """Stamp `tenant_id` + `owner_id` onto a create payload from auth.

    Idempotent — never overwrites caller-provided values WITH client values;
    the auth context is the source of truth for tenant/owner. This guards
    against payload spoofing. RLS WITH CHECK would still reject mismatched
    tenant_id, but failing here is clearer.
    """
    auth: Auth | None = request.scope.get("auth")
    if auth is None:
        return payload
    if not auth.tenant_id:
        raise PermissionDeniedException("Tenant context required for this operation.")
    if auth.tenant_id:
        payload["tenant_id"] = auth.tenant_id
    user = getattr(auth, "user", None)
    if user is not None and getattr(user, "id", None):
        payload["owner_id"] = user.id
    # Sanitize client-supplied identity fields that must come from auth.
    payload.pop("created_by", None)
    payload.pop("updated_by", None)
    return payload


def strip_identity_fields(payload: dict[str, Any]) -> dict[str, Any]:
    """Remove client-controlled ownership fields from update payloads."""
    for field in IDENTITY_FIELDS:
        payload.pop(field, None)
    return payload


async def enforce_view_or_404(
    service: Any,
    *,
    request: Request,
    resource: Any,
    resource_type: str,
) -> None:
    """Raise 404 if the caller cannot view `resource`. No-op if auth is off."""
    auth: Auth | None = request.scope.get("auth")
    if auth is None:
        return
    allowed = await PermissionService.can(
        service.repository.session,
        auth=auth,
        action="view",
        resource_type=resource_type,
        resource=resource,
    )
    if not allowed:
        raise NotFoundException(f"{resource_type[:-1].capitalize()} not found")


async def enforce_action_or_403(
    service: Any,
    *,
    request: Request,
    action: str,
    resource: Any,
    resource_type: str,
) -> None:
    """Raise 404 if view fails, then 403 if the specific action fails."""
    auth: Auth | None = request.scope.get("auth")
    if auth is None:
        return
    session = service.repository.session
    if not await PermissionService.can(
        session,
        auth=auth,
        action="view",
        resource_type=resource_type,
        resource=resource,
    ):
        raise NotFoundException(f"{resource_type[:-1].capitalize()} not found")
    if not await PermissionService.can(
        session,
        auth=auth,
        action=action,
        resource_type=resource_type,
        resource=resource,
    ):
        raise PermissionDeniedException(
            f"You don't have permission to {action} this {resource_type[:-1]}"
        )


async def attach_permissions(
    service: Any,
    schema: Any,
    obj: Any,
    *,
    request: Request,
    resource_type: str,
) -> Any:
    """Compute `_permissions` and attach onto a serialized Pydantic schema.

    Caller is responsible for the model_serializer wrap that renames
    `permissions` → `_permissions` on the wire (see `agents/schemas.py` for
    the canonical example).
    """
    auth: Auth | None = request.scope.get("auth")
    if auth is None or not hasattr(schema, "permissions"):
        return schema
    session = service.repository.session
    try:
        # SAVEPOINT — if compute_record_permissions raises, only the inner
        # work is rolled back; the outer txn keeps serving the list query.
        async with session.begin_nested():
            schema.permissions = await PermissionService.compute_record_permissions(
                session,
                auth=auth,
                resource_type=resource_type,
                resource=obj,
            )
    except Exception:
        logger.exception(
            "compute_record_permissions failed; omitting _permissions block",
            extra={"resource_type": resource_type},
        )
    return schema


async def serialize_with_permissions(
    service: Any,
    obj: Any,
    *,
    schema_type: Any,
    request: Request,
    resource_type: str,
) -> Any:
    schema = service.to_schema(obj, schema_type=schema_type)
    return await attach_permissions(
        service,
        schema,
        obj,
        request=request,
        resource_type=resource_type,
    )


async def list_with_record_permissions(
    service: Any,
    filters: list[Any],
    *,
    request: Request,
    model: Any,
    schema_type: Any,
    resource_type: str,
) -> Any:
    """List records with record visibility filtering and `_permissions`."""
    extra_filters: list[Any] = list(filters)
    where = await visibility_filter_for(
        service,
        request=request,
        model=model,
        resource_type=resource_type,
    )
    if where is not None:
        extra_filters.append(where)

    results, total = await service.list_and_count(*extra_filters)
    page = service.to_schema(results, total, filters=filters, schema_type=schema_type)
    if request.scope.get("auth") is not None and page.items:
        for item, obj in zip(page.items, results):
            await attach_permissions(
                service,
                item,
                obj,
                request=request,
                resource_type=resource_type,
            )
    return page


async def create_with_record_context(
    service: Any,
    data: Any,
    *,
    model: Any,
    schema_type: Any,
    request: Request,
    resource_type: str,
    audit_username: str | None,
) -> Any:
    """Create a tenant-scoped record with tenant/owner from auth context."""
    payload = data.model_dump(exclude_unset=True)
    payload = force_create_fields(payload, request=request)
    payload["created_by"] = audit_username
    payload["updated_by"] = audit_username
    obj = await service.create(model(**payload), auto_commit=True)
    return await serialize_with_permissions(
        service,
        obj,
        schema_type=schema_type,
        request=request,
        resource_type=resource_type,
    )


async def get_by_code_with_record_access(
    service: Any,
    code: str,
    *,
    model: Any,
    schema_type: Any,
    request: Request,
    resource_type: str,
) -> Any:
    obj = await service.get_one(tenant_system_name_filter(request, model, code))
    await enforce_view_or_404(
        service,
        request=request,
        resource=obj,
        resource_type=resource_type,
    )
    return await serialize_with_permissions(
        service,
        obj,
        schema_type=schema_type,
        request=request,
        resource_type=resource_type,
    )


async def get_by_id_with_record_access(
    service: Any,
    item_id: Any,
    *,
    schema_type: Any,
    request: Request,
    resource_type: str,
) -> Any:
    obj = await service.get(item_id)
    await enforce_view_or_404(
        service,
        request=request,
        resource=obj,
        resource_type=resource_type,
    )
    return await serialize_with_permissions(
        service,
        obj,
        schema_type=schema_type,
        request=request,
        resource_type=resource_type,
    )


async def update_with_record_access(
    service: Any,
    item_id: Any,
    data: Any,
    *,
    schema_type: Any,
    request: Request,
    resource_type: str,
    audit_username: str | None,
    update_payload_hook: Any | None = None,
) -> Any:
    existing = await service.get(item_id)
    await enforce_action_or_403(
        service,
        request=request,
        action="edit",
        resource=existing,
        resource_type=resource_type,
    )
    update_data = strip_identity_fields(data.model_dump(exclude_unset=True))
    if update_payload_hook is not None:
        update_payload_hook(update_data)
    update_data["updated_by"] = audit_username
    obj = await service.update(update_data, item_id=item_id, auto_commit=True)
    return await serialize_with_permissions(
        service,
        obj,
        schema_type=schema_type,
        request=request,
        resource_type=resource_type,
    )


async def delete_with_record_access(
    service: Any,
    item_id: Any,
    *,
    request: Request,
    resource_type: str,
) -> None:
    existing = await service.get(item_id)
    await enforce_action_or_403(
        service,
        request=request,
        action="delete",
        resource=existing,
        resource_type=resource_type,
    )
    _ = await service.delete(item_id)


async def visibility_filter_for(
    service: Any,
    *,
    request: Request,
    model: Any,
    resource_type: str,
) -> Any | None:
    """Build a SQLAlchemy WHERE clause for the caller's record visibility.

    Returns None when auth is absent (test mode); callers should skip
    filtering in that case.
    """
    auth: Auth | None = request.scope.get("auth")
    if auth is None:
        return None
    session = service.repository.session
    try:
        # SAVEPOINT — without it a failing sub-query (e.g. against
        # user_departments / resource_access_grants) aborts the outer txn,
        # and every subsequent statement in this request fails with
        # InFailedSQLTransactionError.
        async with session.begin_nested():
            return await record_visibility_filter(
                session,
                auth=auth,
                model=model,
                resource_type=resource_type,
            )
    except Exception:
        logger.exception(
            "record_visibility_filter failed; falling back to RLS only",
            extra={"resource_type": resource_type},
        )
        return None


def tenant_system_name_filter(request: Request, model: Any, code: str) -> Any:
    """Filter lookup by tenant + system_name for tenant-scoped code routes."""
    auth: Auth | None = request.scope.get("auth")
    if auth is None:
        return model.system_name == code
    if not auth.tenant_id:
        raise PermissionDeniedException("Tenant context required for this operation.")
    return (model.tenant_id == auth.tenant_id) & (model.system_name == code)
