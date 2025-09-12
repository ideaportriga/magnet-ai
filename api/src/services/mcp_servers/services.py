import json
import os
from logging import getLogger

from bson import ObjectId
from cryptography.fernet import Fernet
from mcp.types import CallToolResult, Tool

from stores import get_db_client
from utils.datetime_utils import utc_now

from .remote_client import init_client_session
from .types import (
    McpServerConfigEntity,
    McpServerConfigPersisted,
    McpServerConfigWithSecrets,
    McpServerSessionParams,
    McpServerUpdate,
)

logger = getLogger(__name__)

client = get_db_client()

env = os.environ
SECRET_ENCRYPTION_KEY = env.get("SECRET_ENCRYPTION_KEY", "")

COLLECTION_NAME = "mcp_servers"


def encrypt_secrets(secrets: dict[str, str]) -> str:
    if not SECRET_ENCRYPTION_KEY:
        logger.error("Cannot encrypt secrets - SECRET_ENCRYPTION_KEY is not set.")
        raise Exception()

    fernet = Fernet(SECRET_ENCRYPTION_KEY)
    secrets_string = json.dumps(secrets).encode("utf-8")
    secrets_encrypted = fernet.encrypt(secrets_string).decode("utf-8")

    return secrets_encrypted


def decrypt_secrets(secrets_encrypted: str) -> dict[str, str]:
    if not SECRET_ENCRYPTION_KEY:
        logger.error("Cannot decrypt secrets - SECRET_ENCRYPTION_KEY is not set.")
        raise Exception()

    fernet = Fernet(SECRET_ENCRYPTION_KEY)
    decrypted_data_str = fernet.decrypt(secrets_encrypted.encode("utf-8")).decode(
        "utf-8"
    )

    decrypted_data_dict = json.loads(decrypted_data_str)

    return decrypted_data_dict


async def list_mcp_servers() -> list[McpServerConfigEntity]:
    cursor = client.get_collection(COLLECTION_NAME).find({}, {"secrets_encrypted": 0})
    entities = []
    async for document in cursor:
        entities.append(McpServerConfigEntity(id=str(document.pop("_id")), **document))

    return entities


async def get_mcp_server(id: str) -> McpServerConfigEntity:
    document = await client.get_collection(COLLECTION_NAME).find_one(
        {"_id": ObjectId(id)}
    )

    if not document:
        raise Exception("MCP server not found")

    mcp_server = McpServerConfigEntity(id=str(document.pop("_id")), **document)

    return mcp_server


async def create_mcp_server(
    data: McpServerConfigWithSecrets,
) -> dict:
    data_persisted = McpServerConfigPersisted(
        name=data.name,
        system_name=data.system_name,
        transport=data.transport,
        url=data.url,
        headers=data.headers,
    )

    if data.secrets is not None:
        data_persisted.secrets_encrypted = encrypt_secrets(data.secrets)
        data_persisted.secrets_names = list(data.secrets.keys())

    result = await client.get_collection(COLLECTION_NAME).insert_one({
        **data_persisted.model_dump(),
        "created_at": utc_now(),
    })

    return {"inserted_id": str(result.inserted_id)}


async def update_mcp_server(
    id: str,
    update_data: McpServerUpdate,
) -> None:
    set = {
        "updated_at": utc_now(),
        "name": update_data.name,
        "system_name": update_data.system_name,
        "headers": update_data.headers,
    }

    if update_data.secrets is not None:
        set["secrets_encrypted"] = encrypt_secrets(update_data.secrets)
        set["secrets_names"] = list(update_data.secrets.keys())

    result = await client.get_collection("mcp_servers").update_one(
        {"_id": ObjectId(id)},
        {"$set": set},
    )
    if result.matched_count == 0:
        raise ValueError("MCP server not found")


def decrypt_mcp_server_secrets(
    mcp_server_persisted: McpServerConfigPersisted,
) -> McpServerConfigWithSecrets:
    mcp_server_with_secrets = McpServerConfigWithSecrets(
        name=mcp_server_persisted.name,
        system_name=mcp_server_persisted.system_name,
        transport=mcp_server_persisted.transport,
        url=mcp_server_persisted.url,
        headers=mcp_server_persisted.headers,
        secrets_names=mcp_server_persisted.secrets_names,
        tools=mcp_server_persisted.tools,
    )

    if mcp_server_persisted.secrets_encrypted:
        mcp_server_with_secrets.secrets = decrypt_secrets(
            mcp_server_persisted.secrets_encrypted
        )

    return mcp_server_with_secrets


async def get_mcp_server_with_secrets(
    id: str | None,
    system_name: str | None,
) -> McpServerConfigWithSecrets:
    """For internal use only. Do not expose secrets in API."""

    assert id or system_name, (
        "Cannot get MCP server - id or system_name is not provided"
    )

    query = {"_id": ObjectId(id)} if id else {"system_name": system_name}
    document = await client.get_collection(COLLECTION_NAME).find_one(query)

    if not document:
        raise ValueError(f"MCP server not found ({id=}, {system_name=})")

    mcp_server_with_secrets = McpServerConfigWithSecrets(**document)

    mcp_server_persisted = McpServerConfigPersisted(**document)
    mcp_server_with_secrets = decrypt_mcp_server_secrets(mcp_server_persisted)

    return mcp_server_with_secrets


def get_mcp_server_session_params(
    mcp_server: McpServerConfigWithSecrets,
) -> McpServerSessionParams:
    """For internal use only. Do not expose secrets in API."""

    params = McpServerSessionParams(
        transport=mcp_server.transport,
        url=mcp_server.url,
        headers=mcp_server.headers,
    )

    if params.headers and mcp_server.secrets:
        params.headers = replace_placeholders_in_dict(
            params.headers, mcp_server.secrets
        )

    return params


def replace_placeholders_in_string(string: str, values: dict[str, str]) -> str:
    """
    Replace placeholders in the form {SECRET_NAME} in the string
    with the corresponding values from the secrets dict.
    Ignores missing secrets.
    """

    for key, value in values.items():
        string = string.replace(f"{{{key}}}", str(value))

    return string


def replace_placeholders_in_dict(data: dict[str, str], values: dict[str, str]) -> dict:
    """
    Replace placeholders in the form {SECRET_NAME} in the values of the data dict
    with the corresponding values from the secrets dict.
    Ignores missing secrets.
    """
    result: dict[str, str] = {}
    for dict_key, dict_value in data.items():
        result[dict_key] = replace_placeholders_in_string(dict_value, values)

    return result


async def test_mcp_server_connection(
    id: str | None = None,
    system_name: str | None = None,
) -> None:
    """Test MCP server connection."""

    mcp_server = await get_mcp_server_with_secrets(id, system_name)

    session_params = get_mcp_server_session_params(mcp_server)

    async with init_client_session(session_params):
        return None

async def delete_mcp_server(
    id: str | None = None,
    system_name: str | None = None,
) -> None:
    """Delete MCP server."""

    assert id or system_name, (
        "Cannot get MCP server - id or system_name is not provided"
    )

    query = {"_id": ObjectId(id)} if id else {"system_name": system_name}
    result = await client.get_collection(COLLECTION_NAME).delete_one(query)

    if result.deleted_count == 0:
        raise ValueError("MCP server not found")

    return None


async def sync_mcp_server_tools(
    id: str | None = None,
    system_name: str | None = None,
) -> list[Tool]:
    """Sync MCP server tools."""

    assert id or system_name, (
        "Cannot get MCP server - id or system_name is not provided"
    )

    mcp_server = await get_mcp_server_with_secrets(id, system_name)

    session_params = get_mcp_server_session_params(mcp_server)

    async with init_client_session(session_params) as session:
        # TODO - check pagination
        list_tools_result = await session.list_tools()

        tools_dict = list_tools_result.model_dump().get("tools")

        result = await client.get_collection("mcp_servers").update_one(
            {"_id": ObjectId(id)},
            {"$set": {"tools": tools_dict, "last_synced_at": utc_now()}},
        )

        if result.matched_count == 0:
            raise ValueError("MCP server not found")

        return list_tools_result.tools


async def call_mcp_server_tool(
    tool: str,
    arguments: dict,
    mcp_server_id: str | None = None,
    mcp_server_system_name: str | None = None,
) -> CallToolResult:
    """Sync MCP server tools."""
    mcp_server = await get_mcp_server_with_secrets(
        id=mcp_server_id, system_name=mcp_server_system_name
    )

    session_params = get_mcp_server_session_params(mcp_server)

    async with init_client_session(session_params) as session:
        result = await session.call_tool(
            name=tool,
            arguments=arguments,
        )

        return result
