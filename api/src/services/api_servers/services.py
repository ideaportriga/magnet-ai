from logging import getLogger
from typing import Any

import aiohttp
from bson import ObjectId

from services.api_servers.clients import create_api_client_session
from stores import get_db_client
from utils.datetime_utils import utc_now
from utils.secrets import decrypt_secrets, encrypt_secrets

from .types import (
    ApiServerConfigEntity,
    ApiServerConfigPersisted,
    ApiServerConfigWithSecrets,
    ApiServerUpdate,
    ApiToolCall,
    ApiToolCallResult,
)

logger = getLogger(__name__)

client = get_db_client()

COLLECTION_NAME = "api_servers"


async def list_api_servers() -> list[ApiServerConfigEntity]:
    cursor = client.get_collection(COLLECTION_NAME).find({}, {"secrets_encrypted": 0})
    entities = []
    async for document in cursor:
        entities.append(ApiServerConfigEntity(id=str(document.pop("_id")), **document))

    return entities


async def get_api_server(id: str) -> ApiServerConfigEntity:
    document = await client.get_collection(COLLECTION_NAME).find_one(
        {"_id": ObjectId(id)}
    )

    if not document:
        raise Exception("API server not found")

    api_server = ApiServerConfigEntity(id=str(document.pop("_id")), **document)

    return api_server


async def create_api_server(
    data: ApiServerConfigWithSecrets,
) -> dict:
    data_persisted = ApiServerConfigPersisted(
        name=data.name,
        system_name=data.system_name,
        url=data.url,
        security_scheme=data.security_scheme,
        security_values=data.security_values,
        verify_ssl=data.verify_ssl,
        tools=data.tools,
    )

    if data.secrets is not None:
        data_persisted.secrets_encrypted = encrypt_secrets(data.secrets)
        data_persisted.secrets_names = list(data.secrets.keys())

    result = await client.get_collection(COLLECTION_NAME).insert_one(
        {
            **data_persisted.model_dump(),
            "created_at": utc_now(),
        }
    )

    return {"inserted_id": str(result.inserted_id)}


async def update_api_server(
    id: str,
    update_data: ApiServerUpdate,
) -> None:
    set = {
        "updated_at": utc_now(),
        **update_data.model_dump(exclude_unset=True, exclude={"secrets"}),
    }

    if update_data.secrets is not None:
        set["secrets_encrypted"] = encrypt_secrets(update_data.secrets)
        set["secrets_names"] = list(update_data.secrets.keys())

    result = await client.get_collection(COLLECTION_NAME).update_one(
        {"_id": ObjectId(id)},
        {"$set": set},
    )
    if result.matched_count == 0:
        raise ValueError("API server not found")


def decrypt_api_server_secrets(
    api_server_persisted: ApiServerConfigPersisted,
) -> ApiServerConfigWithSecrets:
    api_server_with_secrets = ApiServerConfigWithSecrets(
        name=api_server_persisted.name,
        system_name=api_server_persisted.system_name,
        url=api_server_persisted.url,
        security_scheme=api_server_persisted.security_scheme,
        security_values=api_server_persisted.security_values,
        secrets_names=api_server_persisted.secrets_names,
        tools=api_server_persisted.tools,
    )

    if api_server_persisted.secrets_encrypted:
        api_server_with_secrets.secrets = decrypt_secrets(
            api_server_persisted.secrets_encrypted
        )

    return api_server_with_secrets


async def get_api_server_with_secrets(
    id: str | None = None,
    system_name: str | None = None,
) -> ApiServerConfigWithSecrets:
    """For internal use only. Do not expose secrets in API."""

    assert id or system_name, (
        "Cannot get API server - id or system_name is not provided"
    )

    query = {"_id": ObjectId(id)} if id else {"system_name": system_name}
    document = await client.get_collection(COLLECTION_NAME).find_one(query)

    if not document:
        raise ValueError(f"API server not found ({id=}, {system_name=})")

    api_server_with_secrets = ApiServerConfigWithSecrets(**document)

    api_server_persisted = ApiServerConfigPersisted(**document)
    api_server_with_secrets = decrypt_api_server_secrets(api_server_persisted)

    return api_server_with_secrets


async def delete_api_server(
    id: str | None = None,
    system_name: str | None = None,
) -> None:
    """Delete API server."""

    assert id or system_name, (
        "Cannot get API server - id or system_name is not provided"
    )

    query = {"_id": ObjectId(id)} if id else {"system_name": system_name}
    result = await client.get_collection(COLLECTION_NAME).delete_one(query)

    if result.deleted_count == 0:
        raise ValueError("API server not found")

    return None


async def call_api_server_tool(api_tool_call: ApiToolCall) -> ApiToolCallResult:
    """Sync API server tools."""
    server = await get_api_server_with_secrets(system_name=api_tool_call.server)

    tool = next(
        (tool for tool in server.tools or [] if tool.system_name == api_tool_call.tool),
        None,
    )

    assert tool, f"API server tool {api_tool_call.tool} not found"

    if tool.mock_response_enabled:
        return ApiToolCallResult(
            content=tool.mock_response.content if tool.mock_response else "",
            headers={},
            status_code=200,
        )

    input_params = api_tool_call.input_params

    url = get_complete_url(
        base_url=server.url,
        path=tool.path,
        path_params=input_params.pathParams,
    )

    # Experimental feature - override header with dynamic value from call variables if "api_key_variable" is defined
    security_scheme_type = (server.security_scheme or {}).get("type")
    if security_scheme_type == "apiKey" and server.security_values:
        api_key_variable = server.security_values.get("api_key_variable")

        if api_key_variable:
            api_key = (api_tool_call.variables or {}).get(api_key_variable, "")
            server.security_values["api_key"] = api_key

    api_client_session = await create_api_client_session(server)

    async with api_client_session as session:
        response = await session.request(
            method=tool.method,
            url=url,
            params=input_params.queryParams,
            json=input_params.requestBody,
        )

        content = await parse_response_content(response)

        result = ApiToolCallResult(
            content=content,
            headers=dict(response.headers),
            status_code=response.status,
        )
        return result


def get_complete_url(
    base_url: str,
    path: str,
    path_params: dict[str, Any] | None = None,
) -> str:
    if path_params:
        for key, value in path_params.items():
            path = path.replace(f"{{{key}}}", str(value))

    url = f"{base_url}{path}"

    return url


async def parse_response_content(response: aiohttp.ClientResponse) -> str:
    # TODO - handle different formats if necessary
    return await response.text()
