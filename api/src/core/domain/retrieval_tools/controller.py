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
    create_with_record_context,
    delete_with_record_access,
    get_by_code_with_record_access,
    get_by_id_with_record_access,
    list_with_record_permissions,
    update_with_record_access,
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

        return await list_with_record_permissions(
            retrieval_tools_service,
            filters,
            request=request,
            model=RetrievalToolModel,
            schema_type=RetrievalTool,
            resource_type=_RESOURCE,
        )

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

        return await create_with_record_context(
            retrieval_tools_service,
            data,
            model=RetrievalToolModel,
            schema_type=RetrievalTool,
            request=request,
            resource_type=_RESOURCE,
            audit_username=audit_username,
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

        return await get_by_code_with_record_access(
            retrieval_tools_service,
            code,
            model=RetrievalToolModel,
            schema_type=RetrievalTool,
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
        return await get_by_id_with_record_access(
            retrieval_tools_service,
            retrieval_tool_id,
            schema_type=RetrievalTool,
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
        return await update_with_record_access(
            retrieval_tools_service,
            retrieval_tool_id,
            data,
            schema_type=RetrievalTool,
            request=request,
            resource_type=_RESOURCE,
            audit_username=audit_username,
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
        await delete_with_record_access(
            retrieval_tools_service,
            retrieval_tool_id,
            request=request,
            resource_type=_RESOURCE,
        )

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
