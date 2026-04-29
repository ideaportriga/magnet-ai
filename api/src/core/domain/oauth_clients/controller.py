"""Admin CRUD for OAuth clients (used by the MCP server's authorization-server side).

TEMPORARY (experimental): write operations (create/update/delete) are currently
open to any authenticated admin while the MCP integration is being developed
and tested. The intended security model is **superuser-only** for write — adding
an OAuth client to your AS is a high-trust operation (it lets that client's
redirect URIs receive auth codes for arbitrary users). Re-enable
`_require_superuser(request)` in create/update/delete before this leaves
experimental status.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from advanced_alchemy.extensions.litestar import filters, providers, service
from litestar import Controller, delete, get, patch, post
from litestar.connection import Request
from litestar.exceptions import ClientException, NotAuthorizedException
from litestar.params import Dependency, Parameter

from core.config.constants import DEFAULT_PAGINATION_SIZE
from core.db.models.oauth.oauth_client import OAuthClient as OAuthClientModel
from core.domain.oauth_clients.service import OAuthClientsService
from utils.secrets import encrypt_string

from .schemas import OAuthClientCreate, OAuthClientResponse, OAuthClientUpdate


def _require_superuser(request: Request) -> None:
    """Reject the request unless the calling user is a superuser.

    Currently unused — see module docstring. Kept so the gate can be restored
    by uncommenting the call sites in create/update/delete.
    """
    auth = request.scope.get("auth")
    if not auth or not auth.user:
        raise NotAuthorizedException("Authentication required")
    if not auth.user.is_superuser:
        raise NotAuthorizedException("Only superusers may manage OAuth clients")


class OAuthClientsController(Controller):
    """OAuth clients admin CRUD."""

    path = "/oauth_clients"
    tags = ["Admin / OAuth Clients"]

    dependencies = providers.create_service_dependencies(
        OAuthClientsService,
        "oauth_clients_service",
        filters={
            "pagination_type": "limit_offset",
            "id_filter": UUID,
            "search": "client_id,name",
            "search_ignore_case": True,
            "pagination_size": DEFAULT_PAGINATION_SIZE,
            "sort_field": "updated_at",
            "sort_order": "desc",
        },
    )

    @get()
    async def list_oauth_clients(
        self,
        oauth_clients_service: OAuthClientsService,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
    ) -> service.OffsetPagination[OAuthClientResponse]:
        """List OAuth clients (admin-readable)."""
        results, total = await oauth_clients_service.list_and_count(*filters)
        items = [OAuthClientResponse.from_model(obj) for obj in results]
        return service.OffsetPagination(
            items=items,
            total=total,
            limit=DEFAULT_PAGINATION_SIZE,
            offset=0,
        )

    @get("/{oauth_client_id:uuid}")
    async def get_oauth_client(
        self,
        oauth_clients_service: OAuthClientsService,
        oauth_client_id: UUID = Parameter(
            title="OAuth Client ID",
            description="The OAuth client to retrieve.",
        ),
    ) -> OAuthClientResponse:
        """Get a single OAuth client."""
        obj = await oauth_clients_service.get(oauth_client_id)
        return OAuthClientResponse.from_model(obj)

    @post()
    async def create_oauth_client(
        self,
        oauth_clients_service: OAuthClientsService,
        data: OAuthClientCreate,
        request: Request,
    ) -> OAuthClientResponse:
        """Register a new OAuth client.

        TEMPORARY: open to any authenticated admin. Should be superuser-only.
        Restore by uncommenting `_require_superuser(request)` below.
        """
        # _require_superuser(request)
        _ = request

        if not data.is_public and not data.client_secret:
            raise ClientException(
                "Confidential clients (is_public=false) require a client_secret"
            )

        existing = await oauth_clients_service.get_one_or_none(client_id=data.client_id)
        if existing is not None:
            raise ClientException(
                f"An OAuth client with client_id '{data.client_id}' already exists"
            )

        encrypted_secret = (
            encrypt_string(data.client_secret) if data.client_secret else None
        )

        obj = OAuthClientModel(
            client_id=data.client_id,
            name=data.name,
            is_public=data.is_public,
            client_secret_encrypted=encrypted_secret,
            redirect_uris=data.redirect_uris,
            enabled=data.enabled,
            created_via="admin",
        )
        created = await oauth_clients_service.create(obj)
        return OAuthClientResponse.from_model(created)

    @patch("/{oauth_client_id:uuid}")
    async def update_oauth_client(
        self,
        oauth_clients_service: OAuthClientsService,
        data: OAuthClientUpdate,
        request: Request,
        oauth_client_id: UUID = Parameter(
            title="OAuth Client ID",
            description="The OAuth client to update.",
        ),
    ) -> OAuthClientResponse:
        """Update an existing OAuth client.

        TEMPORARY: open to any authenticated admin. Should be superuser-only.
        Restore by uncommenting `_require_superuser(request)` below.

        Notes:
          - `client_id` is immutable (drop+recreate to change it).
          - Setting `client_secret` to "" clears the stored secret. Setting it
            to a non-empty value re-encrypts and replaces. Omitting it leaves
            the existing secret intact.
        """
        # _require_superuser(request)
        _ = request

        update_payload: dict = {}
        if data.name is not None:
            update_payload["name"] = data.name
        if data.is_public is not None:
            update_payload["is_public"] = data.is_public
        if data.redirect_uris is not None:
            update_payload["redirect_uris"] = data.redirect_uris
        if data.enabled is not None:
            update_payload["enabled"] = data.enabled
        if data.client_secret is not None:
            update_payload["client_secret_encrypted"] = (
                encrypt_string(data.client_secret) if data.client_secret else None
            )

        obj = await oauth_clients_service.update(
            update_payload, item_id=oauth_client_id, auto_commit=True
        )
        return OAuthClientResponse.from_model(obj)

    @delete("/{oauth_client_id:uuid}")
    async def delete_oauth_client(
        self,
        oauth_clients_service: OAuthClientsService,
        request: Request,
        oauth_client_id: UUID = Parameter(
            title="OAuth Client ID",
            description="The OAuth client to delete.",
        ),
    ) -> None:
        """Delete an OAuth client.

        TEMPORARY: open to any authenticated admin. Should be superuser-only.
        Restore by uncommenting `_require_superuser(request)` below.

        Prefer flipping `enabled=false` over hard-deleting in production —
        deletion cascades into the oauth_authorization_code table and loses
        the audit trail.
        """
        # _require_superuser(request)
        _ = request
        _ = await oauth_clients_service.delete(oauth_client_id)
