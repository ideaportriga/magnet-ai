from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from advanced_alchemy.extensions.litestar import filters, providers, service
from litestar import Controller, delete, get, patch, post
from litestar.connection import Request
from litestar.params import Dependency, Parameter
from litestar.status_codes import HTTP_200_OK

from core.config.constants import DEFAULT_PAGINATION_SIZE
from core.domain.rag_tools.schemas import RagTool, RagToolCreate, RagToolUpdate
from core.domain.rag_tools.service import RagToolsService
from guards.permissions import Permission, require_permission
from services.access_control import (
    attach_permissions,
    enforce_action_or_403,
    enforce_view_or_404,
    force_create_fields,
    visibility_filter_for,
)
from services.observability import observability_context, observe
from services.rag_tools import execute_rag_tool
from services.rag_tools.models import RagToolTestResult
from services.rag_tools.services import get_rag_by_system_name_flat
from validation.rag_tools import RagToolExecute, RagToolTest

logger = logging.getLogger(__name__)
_RESOURCE = "rag_tools"

if TYPE_CHECKING:
    pass


class RagToolsController(Controller):
    """RAG Tools CRUD"""

    path = "/rag_tools"
    tags = ["Admin / RAG Tools"]

    dependencies = providers.create_service_dependencies(
        RagToolsService,
        "rag_tools_service",
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

    @get(guards=[require_permission(Permission.RAG_TOOLS_READ)])
    async def list_rag_tools(
        self,
        rag_tools_service: RagToolsService,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
        request: Request,
    ) -> service.OffsetPagination[RagTool]:
        """List RAG tools — filtered by record-level visibility (PR 10)."""
        from core.db.models.rag_tool.rag_tool import RagTool as RagToolModel

        extra_filters: list = list(filters)
        where = await visibility_filter_for(
            rag_tools_service,
            request=request,
            model=RagToolModel,
            resource_type=_RESOURCE,
        )
        if where is not None:
            extra_filters.append(where)
        results, total = await rag_tools_service.list_and_count(*extra_filters)
        page = rag_tools_service.to_schema(
            results, total, filters=filters, schema_type=RagTool
        )
        if request.scope.get("auth") is not None and page.items:
            for item, model in zip(page.items, results):
                await attach_permissions(
                    rag_tools_service,
                    item,
                    model,
                    request=request,
                    resource_type=_RESOURCE,
                )
        return page

    @post(guards=[require_permission(Permission.RAG_TOOLS_WRITE)])
    async def create_rag_tool(
        self,
        rag_tools_service: RagToolsService,
        data: RagToolCreate,
        request: Request,
        audit_username: str | None,
    ) -> RagTool:
        """Create a new RAG tool. tenant_id + owner_id forced from auth."""
        from core.db.models.rag_tool.rag_tool import RagTool as RagToolModel

        data.created_by = audit_username
        data.updated_by = audit_username
        payload = data.model_dump(exclude_unset=True)
        payload = force_create_fields(payload, request=request)
        payload["created_by"] = audit_username
        payload["updated_by"] = audit_username
        obj = await rag_tools_service.create(RagToolModel(**payload), auto_commit=True)
        schema = rag_tools_service.to_schema(obj, schema_type=RagTool)
        return await attach_permissions(
            rag_tools_service, schema, obj, request=request, resource_type=_RESOURCE
        )

    @get("/code/{code:str}", guards=[require_permission(Permission.RAG_TOOLS_READ)])
    async def get_rag_tool_by_code(
        self, rag_tools_service: RagToolsService, code: str, request: Request
    ) -> RagTool:
        """Get a RAG tool by its system_name."""
        obj = await rag_tools_service.get_one(system_name=code)
        await enforce_view_or_404(
            rag_tools_service,
            request=request,
            resource=obj,
            resource_type=_RESOURCE,
        )
        schema = rag_tools_service.to_schema(obj, schema_type=RagTool)
        return await attach_permissions(
            rag_tools_service, schema, obj, request=request, resource_type=_RESOURCE
        )

    @get("/{rag_tool_id:uuid}", guards=[require_permission(Permission.RAG_TOOLS_READ)])
    async def get_rag_tool(
        self,
        rag_tools_service: RagToolsService,
        request: Request,
        rag_tool_id: UUID = Parameter(
            title="RAG Tool ID",
            description="The RAG tool to retrieve.",
        ),
    ) -> RagTool:
        """Get a RAG tool by its ID. 404 if caller can't view it."""
        obj = await rag_tools_service.get(rag_tool_id)
        await enforce_view_or_404(
            rag_tools_service,
            request=request,
            resource=obj,
            resource_type=_RESOURCE,
        )
        schema = rag_tools_service.to_schema(obj, schema_type=RagTool)
        return await attach_permissions(
            rag_tools_service, schema, obj, request=request, resource_type=_RESOURCE
        )

    @patch(
        "/{rag_tool_id:uuid}", guards=[require_permission(Permission.RAG_TOOLS_WRITE)]
    )
    async def update_rag_tool(
        self,
        rag_tools_service: RagToolsService,
        data: RagToolUpdate,
        request: Request,
        rag_tool_id: UUID = Parameter(
            title="RAG Tool ID",
            description="The RAG tool to update.",
        ),
        audit_username: str | None = None,
    ) -> RagTool:
        """Update a RAG tool. 404/403 per record-level access rules."""
        existing = await rag_tools_service.get(rag_tool_id)
        await enforce_action_or_403(
            rag_tools_service,
            request=request,
            action="edit",
            resource=existing,
            resource_type=_RESOURCE,
        )
        update_data = data.model_dump(exclude_unset=True)
        for forbidden in ("tenant_id", "owner_id"):
            update_data.pop(forbidden, None)
        if "variants" in update_data:
            logger.info(
                "update_rag_tool: variants type=%s",
                type(update_data["variants"]).__name__,
            )
        update_data["updated_by"] = audit_username
        obj = await rag_tools_service.update(
            update_data, item_id=rag_tool_id, auto_commit=True
        )
        schema = rag_tools_service.to_schema(obj, schema_type=RagTool)
        return await attach_permissions(
            rag_tools_service, schema, obj, request=request, resource_type=_RESOURCE
        )

    @delete(
        "/{rag_tool_id:uuid}", guards=[require_permission(Permission.RAG_TOOLS_DELETE)]
    )
    async def delete_rag_tool(
        self,
        rag_tools_service: RagToolsService,
        request: Request,
        rag_tool_id: UUID = Parameter(
            title="RAG Tool ID",
            description="The RAG tool to delete.",
        ),
    ) -> None:
        """Delete a RAG tool. 404/403 per record-level access rules."""
        existing = await rag_tools_service.get(rag_tool_id)
        await enforce_action_or_403(
            rag_tools_service,
            request=request,
            action="delete",
            resource=existing,
            resource_type=_RESOURCE,
        )
        _ = await rag_tools_service.delete(rag_tool_id)

    @observe(name="Previewing RAG Tool", channel="preview")
    @post("/test", status_code=HTTP_200_OK)
    async def test(self, data: RagToolTest, user_id: str | None) -> RagToolTestResult:
        """Test a RAG tool with preview channel."""
        rag_tool_config = await get_rag_by_system_name_flat(data.system_name)

        observability_context.update_current_baggage(
            source="preview",
            consumer_type="rag",
            consumer_name=rag_tool_config.get("name"),
            user_id=user_id,
        )

        observability_context.update_current_trace(
            name=rag_tool_config.get("name"), type="rag", user_id=user_id
        )

        return await execute_rag_tool(
            system_name_or_config=rag_tool_config,
            user_message=data.user_message,
            metadata_filter=data.metadata_filter,
            config_override=data,
            verbose=True,
        )

    @observe(name="Executing RAG Tool", channel="production")
    @post("/execute", status_code=HTTP_200_OK)
    async def execute(
        self,
        data: RagToolExecute,
        user_id: str | None,
        request: Request,  # do not remove this, it is used to get x-attributes in observe decorator
    ) -> RagToolTestResult:
        """Execute a RAG tool in production channel."""
        rag_tool_config = await get_rag_by_system_name_flat(data.system_name)

        observability_context.update_current_baggage(
            source=request.headers.get("x-source"),
            consumer_type=request.headers.get("x-consumer-type") or "rag",
            consumer_name=request.headers.get("x-consumer-name")
            or rag_tool_config.get("system_name"),
            user_id=user_id,
        )

        observability_context.update_current_trace(
            name=rag_tool_config.get("name"), type="rag", user_id=user_id
        )

        return await execute_rag_tool(
            system_name_or_config=rag_tool_config, user_message=data.user_message
        )
