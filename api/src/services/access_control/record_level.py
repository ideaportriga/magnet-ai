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

from typing import Any

from litestar import Request
from litestar.exceptions import NotFoundException, PermissionDeniedException

from middlewares.auth import Auth
from services.access_control.permissions import (
    PermissionService,
    record_visibility_filter,
)


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
    try:
        schema.permissions = await PermissionService.compute_record_permissions(
            service.repository.session,
            auth=auth,
            resource_type=resource_type,
            resource=obj,
        )
    except Exception:
        # Failing closed on permission compute is worse than no _permissions
        # block — the UI will simply not show advanced affordances.
        pass
    return schema


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
    try:
        return await record_visibility_filter(
            service.repository.session,
            auth=auth,
            model=model,
            resource_type=resource_type,
        )
    except Exception:
        # Conservative fallback: don't take the endpoint down — RLS still
        # enforces tenant boundary.
        return None


def tenant_system_name_filter(request: Request, model: Any, code: str) -> Any:
    """Filter lookup by tenant + system_name for tenant-scoped code routes."""
    auth: Auth | None = request.scope.get("auth")
    if auth is None:
        return model.system_name == code
    if not auth.tenant_id:
        raise PermissionDeniedException("Tenant context required for this operation.")
    return (model.tenant_id == auth.tenant_id) & (model.system_name == code)
