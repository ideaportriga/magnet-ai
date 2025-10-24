
from litestar import Controller, delete, get, post

from services.api_keys.types import ApiKeyConfigEntity, CreateApiKeyData, CreateApiKeyResult
from services.api_keys import services


class ApiKeysController(Controller):
    path = "/api_keys"
    tags = ["Admin / API Keys"]

    @get("/", summary="List API keys")
    async def list_api_keys(self) -> list[ApiKeyConfigEntity]:
        return await services.list_api_keys()

    @post("/", summary="Create API key")
    async def create_mcp_server(self, data: CreateApiKeyData) -> CreateApiKeyResult:
        return await services.create_api_key(data)


    @delete("/{id:str}", summary="Delete API key")
    async def delete_mcp_server(self, id: str) -> None:
        return await services.delete_api_key(id)
