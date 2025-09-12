from http import HTTPMethod
from typing import Any

from pydantic import BaseModel, ConfigDict

from services.entities.types import BaseEntityMultiVariant

# TODO - typing for OpenAPI operation (could be taken from FastAPI or litestar after migration)
ApiToolOperationDefinition = dict


class ApiToolParameters(BaseModel):
    input: dict
    output: dict


class ApiToolVariantValue(BaseModel):
    """Editable part of API tool entity."""

    parameters: ApiToolParameters

    model_config = {"extra": "allow"}


class ApiToolMock(BaseModel):
    content: str


class ApiToolBase(BaseModel):
    api_provider: str
    path: str
    method: HTTPMethod
    mock: ApiToolMock | None = None


class ApiTool(ApiToolBase, BaseEntityMultiVariant[ApiToolVariantValue]):
    original_parameters: ApiToolParameters
    original_operation_definition: ApiToolOperationDefinition


# TODO - aliases for snake case?
class ApiToolExecuteInputParams(BaseModel):
    model_config = ConfigDict(
        # extra="forbid",
        strict=True,
    )

    pathParams: dict[str, Any] | None = None
    queryParams: dict[str, Any] | None = None
    requestBody: dict[str, Any] | None = None


class ApiToolExecute(BaseModel):
    system_name: str
    input_params: ApiToolExecuteInputParams
    variables: dict[str, str] | None = None


class ApiToolTest(BaseModel):
    api_tool_config: ApiToolBase
    input_params: ApiToolExecuteInputParams
    variables: dict[str, str] | None = None


class ApiToolExecuteResult(BaseModel):
    status_code: int
    headers: dict
    content: str
