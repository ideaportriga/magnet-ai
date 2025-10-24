from __future__ import annotations

import json
from typing import TYPE_CHECKING, Annotated, Any, Dict, List
from uuid import UUID

import yaml
from advanced_alchemy.extensions.litestar import filters, providers, service
from litestar import Controller, delete, get, patch, post
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.exceptions import ClientException
from litestar.params import Body, Dependency, Parameter
from litestar.status_codes import HTTP_200_OK
from pydantic import BaseModel, Field

from core.config.constants import DEFAULT_PAGINATION_SIZE
from core.domain.api_servers.service import (
    ApiServersService,
)
from services.api_servers import services
from services.api_servers.parse_openapi_spec import parse_openapi_spec
from services.api_servers.types import (
    ApiToolCall,
    ApiToolCallResult,
    ParsedOpenApiSpec,
)

from .schemas import ApiServerCreate, ApiServerResponse, ApiServerUpdate

if TYPE_CHECKING:
    pass


class ParseOpenApiSpecTextRequest(BaseModel):
    spec: str


class SecretsUpdateRequest(BaseModel):
    """Schema for partial secrets update."""

    secrets: Dict[str, Any] = Field(..., description="Secrets to update/add")


class SecretsDeleteRequest(BaseModel):
    """Schema for deleting specific secret keys."""

    keys: List[str] = Field(..., description="List of secret keys to delete")


class ApiServersController(Controller):
    """API servers CRUD"""

    path = "/api_servers"
    tags = ["Admin / API Servers"]

    dependencies = providers.create_service_dependencies(
        ApiServersService,
        "api_servers_service",
        filters={
            "pagination_type": "limit_offset",
            "id_filter": UUID,
            "search": "name",
            "search_ignore_case": True,
            "pagination_size": DEFAULT_PAGINATION_SIZE,
        },
    )

    @get()
    async def list_api_servers(
        self,
        api_servers_service: ApiServersService,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
    ) -> service.OffsetPagination[ApiServerResponse]:
        """List API servers with pagination and filtering."""
        results, total = await api_servers_service.list_and_count(*filters)
        return api_servers_service.to_schema(
            results, total, filters=filters, schema_type=ApiServerResponse
        )

    @post()
    async def create_api_server(
        self, api_servers_service: ApiServersService, data: ApiServerCreate
    ) -> ApiServerResponse:
        """Create a new API server."""
        obj = await api_servers_service.create(data)
        return api_servers_service.to_schema(obj, schema_type=ApiServerResponse)

    @get("/code/{code:str}")
    async def get_api_server_by_code(
        self, api_servers_service: ApiServersService, code: str
    ) -> ApiServerResponse:
        """Get an API server by its system_name."""
        obj = await api_servers_service.get_one(system_name=code)
        return api_servers_service.to_schema(obj, schema_type=ApiServerResponse)

    @get("/{api_server_id:uuid}")
    async def get_api_server(
        self,
        api_servers_service: ApiServersService,
        api_server_id: UUID = Parameter(
            title="API Server ID",
            description="The API server to retrieve.",
        ),
    ) -> ApiServerResponse:
        """Get an API server by its ID."""
        obj = await api_servers_service.get(api_server_id)
        return api_servers_service.to_schema(obj, schema_type=ApiServerResponse)

    @patch("/{api_server_id:uuid}")
    async def update_api_server(
        self,
        api_servers_service: ApiServersService,
        data: ApiServerUpdate,
        api_server_id: UUID = Parameter(
            title="API Server ID",
            description="The API server to update.",
        ),
    ) -> ApiServerResponse:
        """Update an API server."""
        obj = await api_servers_service.update(
            data, item_id=api_server_id, auto_commit=True
        )
        return api_servers_service.to_schema(obj, schema_type=ApiServerResponse)

    @delete("/{api_server_id:uuid}")
    async def delete_api_server(
        self,
        api_servers_service: ApiServersService,
        api_server_id: UUID = Parameter(
            title="API Server ID",
            description="The API server to delete.",
        ),
    ) -> None:
        """Delete an API server from the system."""
        _ = await api_servers_service.delete(api_server_id)

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
