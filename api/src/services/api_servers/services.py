from logging import getLogger
from typing import Any

import aiohttp

from core.config.app import alchemy
from core.domain.api_servers.service import ApiServersService
from services.api_servers.clients import create_api_client_session

from .types import (
    ApiServerConfigWithSecrets,
    ApiToolCall,
    ApiToolCallResult,
)

logger = getLogger(__name__)


async def call_api_server_tool(api_tool_call: ApiToolCall) -> ApiToolCallResult:
    """Call API server tool using domain service."""
    async with alchemy.get_session() as session:
        api_servers_service = ApiServersService(session=session)

        # Get API server with secrets by system_name
        api_server_schema = await api_servers_service.get_with_secrets_by_system_name(
            api_tool_call.server
        )

        # Create service config with secrets
        server_config = ApiServerConfigWithSecrets(
            name=api_server_schema.name,
            system_name=api_server_schema.system_name,
            url=api_server_schema.url,
            security_scheme=api_server_schema.security_scheme,
            security_values=api_server_schema.security_values,
            verify_ssl=api_server_schema.verify_ssl,
            tools=[],  # Will convert tools below
            secrets=api_server_schema.secrets_encrypted,  # These are actually unencrypted in the domain schema
        )

        # Convert tools from domain to service format
        if api_server_schema.tools:
            from .types import ApiTool, ApiToolMockResponse, ApiToolParameters

            service_tools = []
            for domain_tool in api_server_schema.tools:
                service_tool = ApiTool(
                    system_name=domain_tool.system_name,
                    name=domain_tool.name,
                    description=domain_tool.description,
                    path=domain_tool.path,
                    method=domain_tool.method,
                    parameters=ApiToolParameters(
                        input=domain_tool.parameters.input,
                        output=domain_tool.parameters.output,
                    ),
                    original_operation_definition=domain_tool.original_operation_definition,
                    mock_response_enabled=domain_tool.mock_response_enabled,
                    mock_response=ApiToolMockResponse(
                        content=domain_tool.mock_response.content
                    )
                    if domain_tool.mock_response
                    else None,
                )
                service_tools.append(service_tool)

            server_config.tools = service_tools

        tool = next(
            (
                tool
                for tool in server_config.tools or []
                if tool.system_name == api_tool_call.tool
            ),
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
            base_url=server_config.url,
            path=tool.path,
            path_params=input_params.pathParams,
        )

        # Experimental feature - override header with dynamic value from call variables if "api_key_variable" is defined
        security_scheme_type = (server_config.security_scheme or {}).get("type")
        if security_scheme_type == "apiKey" and server_config.security_values:
            api_key_variable = server_config.security_values.get("api_key_variable")

            if api_key_variable:
                api_key = (api_tool_call.variables or {}).get(api_key_variable, "")
                server_config.security_values["api_key"] = api_key

        api_client_session = await create_api_client_session(server_config)

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
