"""Self-service endpoints for binding an external identity to the current user.

The external surface (Teams bot, Slack bot, CLI device-flow, …) issues a
pairing code; the user signs into the admin UI and posts that code here:

  GET    /api/me/account-link                  → list current bindings
  GET    /api/me/account-link/{code}           → preview a pairing code
  POST   /api/me/account-link/{code}/confirm   → perform the binding
  DELETE /api/me/account-link/{link_id}        → revoke an existing binding

All endpoints require an authenticated session — the acting user's tenant +
id come from ``Auth``, never from the request body.
"""

from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from litestar import Controller, Request, delete, get, post
from litestar.exceptions import (
    ClientException,
    HTTPException,
    NotFoundException,
    PermissionDeniedException,
)
from litestar.status_codes import HTTP_200_OK, HTTP_204_NO_CONTENT, HTTP_409_CONFLICT
from pydantic import BaseModel

from middlewares.auth import Auth
from services.account_link import (
    LinkCodeAlreadyBound,
    LinkCodeNotFound,
    LinkedAccountNotFound,
    consume_link_code,
    list_linked_accounts,
    preview_link_code,
    revoke_linked_account,
)


class AccountLinkPreviewResponse(BaseModel):
    code: str
    provider: str
    channel_kind: Optional[str]
    display_name: Optional[str]
    email: Optional[str]
    extra: Optional[dict[str, Any]]
    expires_at: str  # ISO-8601


class AccountLinkConfirmResponse(BaseModel):
    status: str = "linked"


class LinkedAccountResponse(BaseModel):
    id: str
    provider: str
    account_id: str
    account_email: Optional[str]
    last_login_at: Optional[str]
    created_at: Optional[str]


def _require_auth(request: Request) -> Auth:
    auth: Auth | None = request.scope.get("auth")
    if auth is None or not auth.user_id or not auth.tenant_id:
        raise PermissionDeniedException(
            "Authenticated session required to link an external account."
        )
    return auth


class AccountLinkController(Controller):
    path = "/account-link"
    tags = ["User / Account Link"]

    @get(
        "/",
        summary="List the current user's linked external accounts",
        description=(
            "Returns every ``user_account_oauth`` row owned by the caller, "
            "ready for the 'My linked accounts' UI."
        ),
        status_code=HTTP_200_OK,
    )
    async def list_links(self, request: Request) -> list[LinkedAccountResponse]:
        auth = _require_auth(request)
        rows = await list_linked_accounts(
            user_id=auth.user_id,
            user_tenant_id=auth.tenant_id,
        )
        return [
            LinkedAccountResponse(
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
        summary="Revoke an existing binding",
        description=(
            "Deletes the ``user_account_oauth`` row owned by the caller. "
            "After this, the external surface (e.g. the Teams bot) falls "
            "back to the unlinked flow and prompts ``/link`` again."
        ),
        status_code=HTTP_204_NO_CONTENT,
    )
    async def revoke(self, request: Request, link_id: UUID) -> None:
        auth = _require_auth(request)
        try:
            await revoke_linked_account(
                link_id=link_id,
                user_id=auth.user_id,
                user_tenant_id=auth.tenant_id,
            )
        except LinkedAccountNotFound:
            raise NotFoundException(detail="Linked account not found.")
        except Exception:
            raise ClientException("Failed to revoke linked account.")

    @get(
        "/{code:str}",
        summary="Preview a pairing code",
        description=(
            "Returns the snapshot of the external identity the supplied code "
            "would bind to the current user. Used by the confirm UI."
        ),
        status_code=HTTP_200_OK,
    )
    async def preview(self, request: Request, code: str) -> AccountLinkPreviewResponse:
        _require_auth(request)
        try:
            preview = await preview_link_code(code)
        except LinkCodeNotFound:
            raise NotFoundException(detail="Code not found, expired, or already used.")
        return AccountLinkPreviewResponse(
            code=preview.code,
            provider=preview.provider,
            channel_kind=preview.channel_kind,
            display_name=preview.display_name,
            email=preview.email,
            extra=preview.extra,
            expires_at=preview.expires_at.isoformat(),
        )

    @post(
        "/{code:str}/confirm",
        summary="Bind the external identity to the current user",
        description=(
            "Consumes the pairing code: creates a ``user_account_oauth`` row "
            "linking (provider, subject_id) → current user, runs the channel-"
            "specific post-consume hook (if any), and marks the code used."
        ),
        status_code=HTTP_200_OK,
    )
    async def confirm(self, request: Request, code: str) -> AccountLinkConfirmResponse:
        auth = _require_auth(request)
        try:
            await consume_link_code(
                code=code,
                user_id=auth.user_id,
                user_tenant_id=auth.tenant_id,
            )
        except LinkCodeNotFound:
            raise NotFoundException(detail="Code not found, expired, or already used.")
        except LinkCodeAlreadyBound:
            raise HTTPException(
                status_code=HTTP_409_CONFLICT,
                detail=(
                    "This external identity is already bound to a different "
                    "user. Ask an administrator to detach it first."
                ),
            )
        except Exception:
            raise ClientException("Failed to confirm account link.")

        return AccountLinkConfirmResponse()
