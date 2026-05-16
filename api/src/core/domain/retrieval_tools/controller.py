from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from advanced_alchemy.extensions.litestar import filters, providers, service
from litestar import Controller, delete, get, patch, post
from litestar.connection import Request
from litestar.params import Dependency, Parameter
from litestar.status_codes import HTTP_200_OK

from core.config.constants import DEFAULT_PAGINATION_SIZE
from core.domain.retrieval_tools.schemas import (
    RetrievalTool,
    RetrievalToolCreate,
    RetrievalToolUpdate,
)
from core.domain.retrieval_tools.service import (
    RetrievalToolsService,
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
from services.flow_retrieval_execute import flow_retrieval_execute
from services.flow_retrieval_test import RetrievalToolTestResult, flow_retrieval_test
from services.observability import observability_context, observe
from validation.retrieval_tools import (
    RetrievalToolExecute,
    RetrievalToolTest,
)


_RESOURCE = "retrieval_tools"

if TYPE_CHECKING:
    pass


class RetrievalToolsController(Controller):
    """Retrieval Tools CRUD"""

    path = "/retrieval_tools"
    tags = ["Admin / Retrieval Tools"]

    dependencies = providers.create_service_dependencies(
        RetrievalToolsService,
        "retrieval_tools_service",
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

    @get(guards=[require_permission(Permission.RETRIEVAL_TOOLS_READ)])
    async def list_retrieval_tools(
        self,
        retrieval_tools_service: RetrievalToolsService,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
        request: Request,
    ) -> service.OffsetPagination[RetrievalTool]:
        """List Retrieval tools — filtered by record-level visibility (PR 10)."""
        from core.db.models.retrieval_tool.retrieval_tool import (
            RetrievalTool as RetrievalToolModel,
        )

        extra_filters: list = list(filters)
        where = await visibility_filter_for(
            retrieval_tools_service,
            request=request,
            model=RetrievalToolModel,
            resource_type=_RESOURCE,
        )
        if where is not None:
            extra_filters.append(where)
        results, total = await retrieval_tools_service.list_and_count(*extra_filters)
        page = retrieval_tools_service.to_schema(
            results, total, filters=filters, schema_type=RetrievalTool
        )
        if request.scope.get("auth") is not None and page.items:
            for item, model in zip(page.items, results):
                await attach_permissions(
                    retrieval_tools_service,
                    item,
                    model,
                    request=request,
                    resource_type=_RESOURCE,
                )
        return page

    @post(guards=[require_permission(Permission.RETRIEVAL_TOOLS_WRITE)])
    async def create_retrieval_tool(
        self,
        retrieval_tools_service: RetrievalToolsService,
        data: RetrievalToolCreate,
        request: Request,
        audit_username: str | None,
    ) -> RetrievalTool:
        """Create a new Retrieval tool. tenant_id + owner_id forced from auth."""
        from core.db.models.retrieval_tool.retrieval_tool import (
            RetrievalTool as RetrievalToolModel,
        )

        data.created_by = audit_username
        data.updated_by = audit_username
        payload = data.model_dump(exclude_unset=True)
        payload = force_create_fields(payload, request=request)
        payload["created_by"] = audit_username
        payload["updated_by"] = audit_username
        obj = await retrieval_tools_service.create(
            RetrievalToolModel(**payload), auto_commit=True
        )
        schema = retrieval_tools_service.to_schema(obj, schema_type=RetrievalTool)
        return await attach_permissions(
            retrieval_tools_service,
            schema,
            obj,
            request=request,
            resource_type=_RESOURCE,
        )

    @get(
        "/code/{code:str}",
        guards=[require_permission(Permission.RETRIEVAL_TOOLS_READ)],
    )
    async def get_retrieval_tool_by_code(
        self,
        retrieval_tools_service: RetrievalToolsService,
        code: str,
        request: Request,
    ) -> RetrievalTool:
        """Get a Retrieval tool by its system_name."""
        from core.db.models.retrieval_tool.retrieval_tool import (
            RetrievalTool as RetrievalToolModel,
        )

        obj = await retrieval_tools_service.get_one(
            tenant_system_name_filter(request, RetrievalToolModel, code)
        )
        await enforce_view_or_404(
            retrieval_tools_service,
            request=request,
            resource=obj,
            resource_type=_RESOURCE,
        )
        schema = retrieval_tools_service.to_schema(obj, schema_type=RetrievalTool)
        return await attach_permissions(
            retrieval_tools_service,
            schema,
            obj,
            request=request,
            resource_type=_RESOURCE,
        )

    @get(
        "/{retrieval_tool_id:uuid}",
        guards=[require_permission(Permission.RETRIEVAL_TOOLS_READ)],
    )
    async def get_retrieval_tool(
        self,
        retrieval_tools_service: RetrievalToolsService,
        request: Request,
        retrieval_tool_id: UUID = Parameter(
            title="Retrieval Tool ID",
            description="The Retrieval tool to retrieve.",
        ),
    ) -> RetrievalTool:
        """Get a Retrieval tool by its ID. 404 if caller can't view it."""
        obj = await retrieval_tools_service.get(retrieval_tool_id)
        await enforce_view_or_404(
            retrieval_tools_service,
            request=request,
            resource=obj,
            resource_type=_RESOURCE,
        )
        schema = retrieval_tools_service.to_schema(obj, schema_type=RetrievalTool)
        return await attach_permissions(
            retrieval_tools_service,
            schema,
            obj,
            request=request,
            resource_type=_RESOURCE,
        )

    @patch(
        "/{retrieval_tool_id:uuid}",
        guards=[require_permission(Permission.RETRIEVAL_TOOLS_WRITE)],
    )
    async def update_retrieval_tool(
        self,
        retrieval_tools_service: RetrievalToolsService,
        data: RetrievalToolUpdate,
        request: Request,
        retrieval_tool_id: UUID = Parameter(
            title="Retrieval Tool ID",
            description="The Retrieval tool to update.",
        ),
        audit_username: str | None = None,
    ) -> RetrievalTool:
        """Update a Retrieval tool. 404/403 per record-level access rules."""
        existing = await retrieval_tools_service.get(retrieval_tool_id)
        await enforce_action_or_403(
            retrieval_tools_service,
            request=request,
            action="edit",
            resource=existing,
            resource_type=_RESOURCE,
        )
        update_data = data.model_dump(exclude_unset=True)
        for forbidden in ("tenant_id", "owner_id"):
            update_data.pop(forbidden, None)
        update_data["updated_by"] = audit_username
        obj = await retrieval_tools_service.update(
            update_data, item_id=retrieval_tool_id, auto_commit=True
        )
        schema = retrieval_tools_service.to_schema(obj, schema_type=RetrievalTool)
        return await attach_permissions(
            retrieval_tools_service,
            schema,
            obj,
            request=request,
            resource_type=_RESOURCE,
        )

    @delete(
        "/{retrieval_tool_id:uuid}",
        guards=[require_permission(Permission.RETRIEVAL_TOOLS_DELETE)],
    )
    async def delete_retrieval_tool(
        self,
        retrieval_tools_service: RetrievalToolsService,
        request: Request,
        retrieval_tool_id: UUID = Parameter(
            title="Retrieval Tool ID",
            description="The Retrieval tool to delete.",
        ),
    ) -> None:
        """Delete a Retrieval tool. 404/403 per record-level access rules."""
        existing = await retrieval_tools_service.get(retrieval_tool_id)
        await enforce_action_or_403(
            retrieval_tools_service,
            request=request,
            action="delete",
            resource=existing,
            resource_type=_RESOURCE,
        )
        _ = await retrieval_tools_service.delete(retrieval_tool_id)

    @observe(name="Previewing Retrieval Tool", channel="preview")
    @post("/test", status_code=HTTP_200_OK)
    async def retrieval_tool_test(
        self, data: RetrievalToolTest
    ) -> RetrievalToolTestResult:
        """Test a Retrieval tool with preview channel."""
        observability_context.update_current_trace(
            name=data.name, type="retrieval-tool"
        )

        result = await flow_retrieval_test(data)

        return result

    @observe(name="Executing Retrieval Tool", channel="production")
    @post("/execute", status_code=HTTP_200_OK)
    async def retrieval_tool_execute(
        self,
        data: RetrievalToolExecute,
        request: Request,  # do not remove this, it is used to get x-attributes in observe decorator
    ) -> RetrievalToolTestResult:
        """Execute a Retrieval tool in production channel."""
        observability_context.update_current_trace(
            name=data.name, type="retrieval-tool"
        )

        result = await flow_retrieval_execute(data)

        return result
