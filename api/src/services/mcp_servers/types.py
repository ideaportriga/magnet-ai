from datetime import datetime
from enum import StrEnum
from typing import Annotated

from mcp.types import Tool
from pydantic import BaseModel, StringConstraints

# TODO - reuse for other entities?
SystemName = Annotated[
    str,
    StringConstraints(
        pattern=r"^[a-zA-Z0-9_]+$",
    ),
]


class McpTransportProtocol(StrEnum):
    SSE = "sse"
    STREAMABLE_HTTP = "streamable-http"


class McpServerSessionParams(BaseModel):
    transport: McpTransportProtocol
    url: str
    headers: dict[str, str] | None = None


# class McpServerTool(BaseModel):
#     name: SystemName
#     description: str
#     # Optional?
#     inputSchema: dict
#     annotations: dict | None


class McpServerConfig(BaseModel):
    name: str
    system_name: SystemName
    transport: McpTransportProtocol
    url: str
    headers: dict[str, str] | None = None
    secrets_names: list[str] | None = None
    tools: list[Tool] | None = None


class McpServerConfigEntity(McpServerConfig):
    id: str
    created_at: datetime
    updated_at: datetime | None = None
    last_synced_at: datetime | None = None


class McpServerConfigPersisted(McpServerConfig):
    secrets_encrypted: str | None = None


class McpServerConfigWithSecrets(McpServerConfig):
    secrets: dict[str, str] | None = None


class McpServerUpdate(BaseModel):
    name: str
    system_name: SystemName
    headers: dict[str, str] | None = None
    secrets: dict[str, str] | None = None
