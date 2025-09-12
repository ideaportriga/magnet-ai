import os
from logging import getLogger
from typing import Any

import aiohttp

from config.api_tool_providers import (
    API_TOOL_PROVIDER_CONFIG_MAPPING,
    PROVIDER_CONFIG_MOCK,
)
from services.api_tools.clients import create_api_client
from services.api_tools.types import ApiToolExecuteResult, ApiToolTest

env = os.environ

logger = getLogger(__name__)


async def api_tool_test(params: ApiToolTest) -> ApiToolExecuteResult:
    api_tool_config = params.api_tool_config
    input_params = params.input_params

    if api_tool_config.api_provider == PROVIDER_CONFIG_MOCK:
        logger.info("Mock API provider is used")
        assert api_tool_config.mock, "Mock is not set up"

        mock_result = ApiToolExecuteResult(
            content=api_tool_config.mock.content,
            headers={},
            status_code=200,
        )

        return mock_result

    api_provider_config = API_TOOL_PROVIDER_CONFIG_MAPPING.get(
        api_tool_config.api_provider,
    )
    assert api_provider_config, (
        f"API provider config is missing for provider {api_tool_config.api_provider}"
    )
    server_url = api_provider_config.get("server_url", {})
    auth_params = api_provider_config.get("auth_params", {})
    security_schema = api_provider_config.get("security_schema", {})

    path = api_tool_config.path
    method = api_tool_config.method.upper()

    url = get_complete_url(
        base_url=server_url,
        path=path,
        path_params=input_params.pathParams,
    )

    api_key_variable = auth_params.get("api_key_variable", "")
    if security_schema.get("type") == "apiKey" and api_key_variable:
        auth_params["api_key"] = (params.variables or {}).get(api_key_variable, "")
    api_client = await create_api_client(
        security_schema=security_schema, 
        auth_params=auth_params,
    )

    try:
        async with api_client.request(
            method,
            url,
            params=input_params.queryParams,
            json=input_params.requestBody,
        ) as response:
            content = await parse_response_content(response)
            result = ApiToolExecuteResult(
                content=content,
                headers=dict(response.headers),
                status_code=response.status,
            )
            return result
    finally:
        await api_client.close()


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
