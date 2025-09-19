import json
from typing import Annotated

import yaml
from litestar import Controller, post
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.exceptions import ClientException
from litestar.params import Body
from litestar.status_codes import HTTP_200_OK
from pydantic import BaseModel

from services.api_servers import services
from services.api_servers.parse_openapi_spec import parse_openapi_spec
from services.api_servers.types import (
    ApiToolCall,
    ApiToolCallResult,
    ParsedOpenApiSpec,
)


class ParseOpenApiSpecTextRequest(BaseModel):
    spec: str


class ApiServersController(Controller):
    path = "/api_servers"
    tags = ["api_servers"]

    @post("/parse_openapi_spec_text", status_code=HTTP_200_OK)
    async def parse_openapi_spec_text(
        self,
        data: ParseOpenApiSpecTextRequest,
    ) -> ParsedOpenApiSpec:
        content = data.spec

        try:
            openapi_spec_raw = json.loads(content)
        except json.JSONDecodeError:
            try:
                openapi_spec_raw = yaml.safe_load(content)
            except yaml.YAMLError:
                raise ValueError("Input is neither valid JSON nor valid YAML.")

        parsed_spec = await parse_openapi_spec(openapi_spec_raw)

        return parsed_spec

    @post("/parse_openapi_spec_file", status_code=HTTP_200_OK)
    async def parse_openapi_spec_file(
        self,
        data: Annotated[UploadFile, Body(media_type=RequestEncodingType.MULTI_PART)],
    ) -> ParsedOpenApiSpec:
        file = data

        if not file:
            raise ClientException("No file provided")

        if not file.filename:
            raise ClientException(detail="No filename")

        content = await file.read()

        if file.filename.endswith(".json"):
            openapi_spec_raw = json.loads(content)
        elif file.filename.endswith(".yml") or file.filename.endswith(".yaml"):
            openapi_spec_raw = yaml.safe_load(content)
        else:
            raise ClientException("Not supported file format")

        parsed_spec = await parse_openapi_spec(openapi_spec_raw)

        return parsed_spec

    @post(
        "/call_tool",
        summary="Call API server tool",
        status_code=HTTP_200_OK,
    )
    async def call_api_server_tool(self, data: ApiToolCall) -> ApiToolCallResult:
        return await services.call_api_server_tool(data)
