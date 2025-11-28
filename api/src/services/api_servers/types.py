from datetime import datetime
from http import HTTPMethod
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, StringConstraints

SystemName = Annotated[
    str,
    StringConstraints(
        pattern=r"^[a-zA-Z0-9_]+$",
    ),
]


# TODO - typing for OpenAPI operation (could be taken from FastAPI or litestar after migration)
ApiToolOperationDefinition = dict


class ApiToolParameters(BaseModel):
    input: dict
    output: dict


class ApiToolMockResponse(BaseModel):
    content: str


class ApiTool(BaseModel):
    system_name: SystemName
    name: str
    description: str | None = None
    path: str
    method: HTTPMethod
    parameters: ApiToolParameters
    original_operation_definition: ApiToolOperationDefinition
    mock_response_enabled: bool = False
    mock_response: ApiToolMockResponse | None = None


class ParsedOpenApiSpec(BaseModel):
    name: str
    tools: list[ApiTool]
    servers: list[dict] | None = None
    security_schemes: dict | None = None


class ApiServerConfig(BaseModel):
    name: str
    system_name: SystemName
    url: str
    security_scheme: dict[str, Any] | None = None
    security_values: dict[str, str] | None = None
    secrets_names: list[str] | None = None
    verify_ssl: bool = True
    tools: list[ApiTool] | None = None


class ApiServerConfigEntity(ApiServerConfig):
    id: str
    created_at: datetime
    updated_at: datetime | None = None


class ApiServerConfigPersisted(ApiServerConfig):
    secrets_encrypted: str | None = None


class ApiServerConfigWithSecrets(ApiServerConfig):
    secrets: dict[str, str] | None = None


class ApiServerUpdate(BaseModel):
    name: str | None = None
    system_name: SystemName | None = None
    security_scheme: dict[str, Any] | None = None
    security_values: dict[str, str] | None = None
    secrets: dict[str, str] | None = None
    verify_ssl: bool = True
    tools: list[ApiTool] | None = None


class ApiToolCallInputParams(BaseModel):
    model_config = ConfigDict(
        # extra="forbid",
        strict=True,
    )

    pathParams: dict[str, Any] | None = None
    queryParams: dict[str, Any] | None = None
    requestBody: dict[str, Any] | None = None


class ApiToolCall(BaseModel):
    server: str
    tool: str
    input_params: ApiToolCallInputParams
    variables: dict[str, str] | None = None


class ApiToolCallResult(BaseModel):
    status_code: int
    headers: dict
    content: str
