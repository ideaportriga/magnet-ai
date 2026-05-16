from litestar import Controller, Request, delete, get, patch, post

from services.api_keys.types import (
    ApiKeyConfigEntity,
    CreateApiKeyData,
    CreateApiKeyResult,
    UpdateApiKeyData,
)
from services.api_keys import services
from guards.permissions import Permission, require_permission
from middlewares.auth import Auth


def _tenant_id_from_request(request: Request) -> str:
    auth: Auth | None = request.scope.get("auth")
    if auth is None or not auth.tenant_id:
        from litestar.exceptions import PermissionDeniedException

        raise PermissionDeniedException("Tenant context required for API keys.")
    return auth.tenant_id


def _auth_from_request(request: Request) -> Auth | None:
    return request.scope.get("auth")


class ApiKeysController(Controller):
    path = "/api_keys"
    tags = ["Admin / API Keys"]

    @get(
        "/",
        summary="List API keys",
        guards=[require_permission(Permission.API_KEYS_READ)],
    )
    async def list_api_keys(self, request: Request) -> list[ApiKeyConfigEntity]:
        return await services.list_api_keys(_tenant_id_from_request(request))

    @get(
        "/{id:str}",
        summary="Get API key",
        guards=[require_permission(Permission.API_KEYS_READ)],
    )
    async def get_api_key(self, request: Request, id: str) -> ApiKeyConfigEntity:
        return await services.get_api_key(id, _tenant_id_from_request(request))

    @post(
        "/",
        summary="Create API key",
        guards=[require_permission(Permission.API_KEYS_WRITE)],
    )
    async def create_mcp_server(
        self, request: Request, data: CreateApiKeyData
    ) -> CreateApiKeyResult:
        return await services.create_api_key(
            data,
            _tenant_id_from_request(request),
            auth=_auth_from_request(request),
        )

    @patch(
        "/{id:str}",
        summary="Update API key",
        guards=[require_permission(Permission.API_KEYS_WRITE)],
    )
    async def update_api_key(
        self, request: Request, id: str, data: UpdateApiKeyData
    ) -> ApiKeyConfigEntity:
        return await services.update_api_key(
            id,
            data,
            _tenant_id_from_request(request),
            auth=_auth_from_request(request),
        )

    @delete(
        "/{id:str}",
        summary="Delete API key",
        guards=[require_permission(Permission.API_KEYS_WRITE)],
    )
    async def delete_mcp_server(self, request: Request, id: str) -> None:
        return await services.delete_api_key(id, _tenant_id_from_request(request))
