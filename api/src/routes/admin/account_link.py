"""Admin-side surface for managing account-link bindings across users.

Used when an admin needs to clean up a wrong binding (e.g. a Teams user
typed someone else's pairing code and bound to the wrong user). The
self-service ``/api/me/account-link/...`` endpoints only operate on the
caller's own bindings, so this is the dedicated admin path:

  GET    /api/admin/account-link            → list bindings in tenant
                                              (optional ``?user_id=...``)
  DELETE /api/admin/account-link/{link_id}  → force-revoke any binding

RLS scopes both reads and writes to the admin's tenant; the route guard
restricts who can call this in the first place.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from litestar import Controller, Request, delete, get
from litestar.exceptions import (
    ClientException,
    NotFoundException,
    PermissionDeniedException,
)
from litestar.status_codes import HTTP_200_OK, HTTP_204_NO_CONTENT
from pydantic import BaseModel

from guards.permissions import Permission, require_permission
from middlewares.auth import Auth
from services.account_link import (
    LinkedAccountNotFound,
    admin_list_linked_accounts,
    admin_revoke_linked_account,
)


class AdminLinkedAccountResponse(BaseModel):
    id: str
    provider: str
    account_id: str
    account_email: Optional[str]
    last_login_at: Optional[str]
    created_at: Optional[str]


def _require_auth(request: Request) -> Auth:
    auth: Auth | None = request.scope.get("auth")
    if auth is None or not auth.user_id or not auth.tenant_id:
        raise PermissionDeniedException("Tenant-scoped admin session required.")
    return auth


class AdminAccountLinkController(Controller):
    path = "/account-link"
    tags = ["Admin / Account Link"]

    @get(
        "/",
        summary="List external-identity bindings in the current tenant",
        description=(
            "Optional ``user_id`` query param narrows the list to a single "
            "user. Without it, returns every binding the tenant owns."
        ),
        guards=[require_permission(Permission.USERS_READ)],
        status_code=HTTP_200_OK,
    )
    async def admin_list(
        self,
        request: Request,
        user_id: UUID | None = None,
    ) -> list[AdminLinkedAccountResponse]:
        auth = _require_auth(request)
        rows = await admin_list_linked_accounts(
            tenant_id=UUID(auth.tenant_id),
            actor_id=UUID(auth.user_id),
            user_id=user_id,
        )
        return [
            AdminLinkedAccountResponse(
                id=str(row.id),
                provider=row.provider,
                account_id=row.account_id,
                account_email=row.account_email,
                last_login_at=row.last_login_at.isoformat()
                if row.last_login_at
                else None,
                created_at=row.created_at.isoformat() if row.created_at else None,
            )
            for row in rows
        ]

    @delete(
        "/{link_id:uuid}",
        summary="Revoke a binding (admin override)",
        description=(
            "Force-deletes a ``user_account_oauth`` row regardless of owner, "
            "as long as it's in the calling admin's tenant. Writes an "
            "``account_link.admin_revoke`` audit row."
        ),
        guards=[require_permission(Permission.USERS_MANAGE)],
        status_code=HTTP_204_NO_CONTENT,
    )
    async def admin_revoke(self, request: Request, link_id: UUID) -> None:
        auth = _require_auth(request)
        try:
            await admin_revoke_linked_account(
                link_id=link_id,
                tenant_id=UUID(auth.tenant_id),
                actor_id=UUID(auth.user_id),
            )
        except LinkedAccountNotFound:
            raise NotFoundException(detail="Linked account not found.")
        except Exception:
            raise ClientException("Failed to revoke linked account.")
