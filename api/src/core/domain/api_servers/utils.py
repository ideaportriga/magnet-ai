"""
Utility functions and schemas for API servers domain.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from services.api_servers.types import (
    ApiServerConfig,
    ApiServerConfigWithSecrets,
)
from services.api_servers.types import (
    ApiTool as ServiceApiTool,
)
from services.api_servers.types import (
    ApiToolMockResponse as ServiceApiToolMockResponse,
)
from services.api_servers.types import (
    ApiToolParameters as ServiceApiToolParameters,
)

from .schemas import ApiServer, ApiTool, ApiToolMockResponse, ApiToolParameters


class ApiServerWithSecrets(BaseModel):
    """API server schema with unencrypted secrets for internal use only."""

    id: str
    name: str
    description: Optional[str] = None
    system_name: str
    category: Optional[str] = None
    url: str
    security_scheme: Optional[Dict[str, Any]] = None
    security_values: Optional[Dict[str, Any]] = None
    verify_ssl: bool = True
    tools: Optional[List[ApiTool]] = None
    secrets: Optional[Dict[str, str]] = None


def convert_domain_to_service_config(api_server: ApiServer) -> ApiServerConfig:
    """Convert domain ApiServer to service ApiServerConfig."""

    # Convert tools if they exist
    service_tools = None
    if api_server.tools:
        service_tools = []
        for tool in api_server.tools:
            # Convert parameters
            service_parameters = ServiceApiToolParameters(
                input=tool.parameters.input,
                output=tool.parameters.output,
            )

            # Convert mock response
            service_mock_response = None
            if tool.mock_response:
                service_mock_response = ServiceApiToolMockResponse(
                    content=tool.mock_response.content
                )

            service_tool = ServiceApiTool(
                system_name=tool.system_name,
                name=tool.name,
                description=tool.description,
                path=tool.path,
                method=tool.method,
                parameters=service_parameters,
                original_operation_definition=tool.original_operation_definition,
                mock_response_enabled=tool.mock_response_enabled,
                mock_response=service_mock_response,
            )
            service_tools.append(service_tool)

    return ApiServerConfig(
        name=api_server.name,
        system_name=api_server.system_name,
        url=api_server.url,
        security_scheme=api_server.security_scheme,
        security_values=api_server.security_values,
        verify_ssl=api_server.verify_ssl,
        tools=service_tools,
    )


def convert_service_to_domain_config(
    service_config: ApiServerConfigWithSecrets,
) -> ApiServer:
    """Convert service ApiServerConfigWithSecrets to domain ApiServer."""

    # Convert tools if they exist
    domain_tools = None
    if service_config.tools:
        domain_tools = []
        for tool in service_config.tools:
            # Convert parameters
            domain_parameters = ApiToolParameters(
                input=tool.parameters.input,
                output=tool.parameters.output,
            )

            # Convert mock response
            domain_mock_response = None
            if tool.mock_response:
                domain_mock_response = ApiToolMockResponse(
                    content=tool.mock_response.content
                )

            domain_tool = ApiTool(
                system_name=tool.system_name,
                name=tool.name,
                description=tool.description,
                path=tool.path,
                method=tool.method,
                parameters=domain_parameters,
                original_operation_definition=tool.original_operation_definition,
                mock_response_enabled=tool.mock_response_enabled,
                mock_response=domain_mock_response,
            )
            domain_tools.append(domain_tool)

    return ApiServer(
        name=service_config.name,
        system_name=service_config.system_name,
        url=service_config.url,
        security_scheme=service_config.security_scheme,
        security_values=service_config.security_values,
        verify_ssl=service_config.verify_ssl,
        tools=domain_tools,
        secrets_encrypted=service_config.secrets,  # For domain, we put secrets in secrets_encrypted
    )
