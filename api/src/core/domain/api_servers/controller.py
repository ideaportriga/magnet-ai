from __future__ import annotations

import json
from typing import TYPE_CHECKING, Annotated, Any, Dict, List
from uuid import UUID

import yaml
from advanced_alchemy.extensions.litestar import filters, providers, service
from litestar import Controller, delete, get, patch, post
from litestar.connection import Request
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
from guards.permissions import Permission, require_permission
from services.access_control import (
    attach_permissions,
    enforce_action_or_403,
    enforce_view_or_404,
    force_create_fields,
    tenant_system_name_filter,
    visibility_filter_for,
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


_RESOURCE = "api_servers"


class ParseOpenApiSpecTextRequest(BaseModel):
    spec: str


class SecretsUpdateRequest(BaseModel):
    """Schema for partial secrets update."""

    secrets: Dict[str, Any] = Field(..., description="Secrets to update/add")


class SecretsDeleteRequest(BaseModel):
    """Schema for deleting specific secret keys."""

    keys: List[str] = Field(..., description="List of secret keys to delete")


class ApiServersController(Controller):
    """API servers CRUD — tenant + record-level scoped (PR 10 rollout)."""

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
            "sort_field": "updated_at",
            "sort_order": "desc",
        },
    )

    @get(guards=[require_permission(Permission.API_SERVERS_READ)])
    async def list_api_servers(
        self,
        api_servers_service: ApiServersService,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
        request: Request,
    ) -> service.OffsetPagination[ApiServerResponse]:
        """List API servers — filtered by record-level visibility."""
        from core.db.models.api_server.api_server import APIServer as APIServerModel

        extra_filters: list = list(filters)
        where = await visibility_filter_for(
            api_servers_service,
            request=request,
            model=APIServerModel,
            resource_type=_RESOURCE,
        )
        if where is not None:
            extra_filters.append(where)
        results, total = await api_servers_service.list_and_count(*extra_filters)
        page = api_servers_service.to_schema(
            results, total, filters=filters, schema_type=ApiServerResponse
        )
        if request.scope.get("auth") is not None and page.items:
            for item, model in zip(page.items, results):
                await attach_permissions(
                    api_servers_service,
                    item,
                    model,
                    request=request,
                    resource_type=_RESOURCE,
                )
        return page

    @post(guards=[require_permission(Permission.API_SERVERS_WRITE)])
    async def create_api_server(
        self,
        api_servers_service: ApiServersService,
        data: ApiServerCreate,
        request: Request,
        audit_username: str | None,
    ) -> ApiServerResponse:
        """Create a new API server. tenant_id + owner_id forced from auth."""
        from core.db.models.api_server.api_server import APIServer as APIServerModel

        data.created_by = audit_username
        data.updated_by = audit_username
        payload = data.model_dump(exclude_unset=True)
        payload = force_create_fields(payload, request=request)
        payload["created_by"] = audit_username
        payload["updated_by"] = audit_username
        obj = await api_servers_service.create(
            APIServerModel(**payload), auto_commit=True
        )
        schema = api_servers_service.to_schema(obj, schema_type=ApiServerResponse)
        return await attach_permissions(
            api_servers_service,
            schema,
            obj,
            request=request,
            resource_type=_RESOURCE,
        )

    @get(
        "/code/{code:str}",
        guards=[require_permission(Permission.API_SERVERS_READ)],
    )
    async def get_api_server_by_code(
        self, api_servers_service: ApiServersService, code: str, request: Request
    ) -> ApiServerResponse:
        """Get an API server by its system_name."""
        from core.db.models.api_server.api_server import APIServer as APIServerModel

        obj = await api_servers_service.get_one(
            tenant_system_name_filter(request, APIServerModel, code)
        )
        await enforce_view_or_404(
            api_servers_service,
            request=request,
            resource=obj,
            resource_type=_RESOURCE,
        )
        schema = api_servers_service.to_schema(obj, schema_type=ApiServerResponse)
        return await attach_permissions(
            api_servers_service,
            schema,
            obj,
            request=request,
            resource_type=_RESOURCE,
        )

    @get(
        "/{api_server_id:uuid}",
        guards=[require_permission(Permission.API_SERVERS_READ)],
    )
    async def get_api_server(
        self,
        api_servers_service: ApiServersService,
        request: Request,
        api_server_id: UUID = Parameter(
            title="API Server ID",
            description="The API server to retrieve.",
        ),
    ) -> ApiServerResponse:
        """Get an API server by its ID. 404 if caller can't view it."""
        obj = await api_servers_service.get(api_server_id)
        await enforce_view_or_404(
            api_servers_service,
            request=request,
            resource=obj,
            resource_type=_RESOURCE,
        )
        schema = api_servers_service.to_schema(obj, schema_type=ApiServerResponse)
        return await attach_permissions(
            api_servers_service,
            schema,
            obj,
            request=request,
            resource_type=_RESOURCE,
        )

    @patch(
        "/{api_server_id:uuid}",
        guards=[require_permission(Permission.API_SERVERS_WRITE)],
    )
    async def update_api_server(
        self,
        api_servers_service: ApiServersService,
        data: ApiServerUpdate,
        request: Request,
        api_server_id: UUID = Parameter(
            title="API Server ID",
            description="The API server to update.",
        ),
        audit_username: str | None = None,
    ) -> ApiServerResponse:
        """Update an API server. 404/403 per record-level access rules."""
        existing = await api_servers_service.get(api_server_id)
        await enforce_action_or_403(
            api_servers_service,
            request=request,
            action="edit",
            resource=existing,
            resource_type=_RESOURCE,
        )
        update_data = data.model_dump(exclude_unset=True)
        for forbidden in ("tenant_id", "owner_id"):
            update_data.pop(forbidden, None)
        update_data["updated_by"] = audit_username
        obj = await api_servers_service.update(
            update_data, item_id=api_server_id, auto_commit=True
        )
        schema = api_servers_service.to_schema(obj, schema_type=ApiServerResponse)
        return await attach_permissions(
            api_servers_service,
            schema,
            obj,
            request=request,
            resource_type=_RESOURCE,
        )

    @delete(
        "/{api_server_id:uuid}",
        guards=[require_permission(Permission.API_SERVERS_DELETE)],
    )
    async def delete_api_server(
        self,
        api_servers_service: ApiServersService,
        request: Request,
        api_server_id: UUID = Parameter(
            title="API Server ID",
            description="The API server to delete.",
        ),
    ) -> None:
        """Delete an API server. 404/403 per record-level access rules."""
        existing = await api_servers_service.get(api_server_id)
        await enforce_action_or_403(
            api_servers_service,
            request=request,
            action="delete",
            resource=existing,
            resource_type=_RESOURCE,
        )
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
