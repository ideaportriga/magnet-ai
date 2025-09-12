import json
from typing import Annotated

import yaml
from litestar import post
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.exceptions import ClientException
from litestar.params import Body
from litestar.status_codes import HTTP_200_OK

from services.api_tools.flow_execute import api_tool_execute
from services.api_tools.flow_test import api_tool_test
from services.api_tools.generate_from_openapi import generate_from_openapi
from services.api_tools.types import (
    ApiTool,
    ApiToolExecute,
    ApiToolExecuteResult,
    ApiToolTest,
)

from .create_entity_controller import create_entity_controller

ApiToolsBaseController = create_entity_controller(
    collection_name="api_tools",
    model=ApiTool,
)


class ApiToolsController(ApiToolsBaseController):
    path = "/api_tools"
    tags = ["api_tools"]

    @post("/generate_from_openapi")
    async def generate_from_openapi_route(
        self,
        data: Annotated[UploadFile, Body(media_type=RequestEncodingType.MULTI_PART)],
    ) -> list[ApiTool]:
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

        tools = await generate_from_openapi(openapi_spec_raw)

        return tools

    @post(
        "/test",
        status_code=HTTP_200_OK,
    )
    async def api_tool_test_route(self, data: ApiToolTest) -> ApiToolExecuteResult:
        result = await api_tool_test(params=data)

        return result

    @post(
        "/execute",
        status_code=HTTP_200_OK,
    )
    async def api_tool_execute_route(
        self,
        data: ApiToolExecute,
    ) -> ApiToolExecuteResult:
        result = await api_tool_execute(params=data)

        return result
