from litestar import Controller, delete, get, patch, post

from services.api_keys.types import (
    ApiKeyConfigEntity,
    CreateApiKeyData,
    CreateApiKeyResult,
    UpdateApiKeyData,
)
from services.api_keys import services


class ApiKeysController(Controller):
    path = "/api_keys"
    tags = ["Admin / API Keys"]

    @get("/", summary="List API keys")
    async def list_api_keys(self) -> list[ApiKeyConfigEntity]:
        return await services.list_api_keys()

    @get("/{id:str}", summary="Get API key")
    async def get_api_key(self, id: str) -> ApiKeyConfigEntity:
        return await services.get_api_key(id)

    @post("/", summary="Create API key")
    async def create_mcp_server(self, data: CreateApiKeyData) -> CreateApiKeyResult:
        return await services.create_api_key(data)

    @patch("/{id:str}", summary="Update API key")
    async def update_api_key(
        self, id: str, data: UpdateApiKeyData
    ) -> ApiKeyConfigEntity:
        return await services.update_api_key(id, data)

    @delete("/{id:str}", summary="Delete API key")
    async def delete_mcp_server(self, id: str) -> None:
        return await services.delete_api_key(id)
