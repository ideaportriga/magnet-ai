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
from services.flow_retrieval_execute import flow_retrieval_execute
from services.flow_retrieval_test import RetrievalToolTestResult, flow_retrieval_test
from services.observability import observability_context, observe
from validation.retrieval_tools import (
    RetrievalToolExecute,
    RetrievalToolTest,
)

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
        },
    )

    @get()
    async def list_retrieval_tools(
        self,
        retrieval_tools_service: RetrievalToolsService,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
    ) -> service.OffsetPagination[RetrievalTool]:
        """List Retrieval tools with pagination and filtering."""
        results, total = await retrieval_tools_service.list_and_count(*filters)
        return retrieval_tools_service.to_schema(
            results, total, filters=filters, schema_type=RetrievalTool
        )

    @post()
    async def create_retrieval_tool(
        self, retrieval_tools_service: RetrievalToolsService, data: RetrievalToolCreate
    ) -> RetrievalTool:
        """Create a new Retrieval tool."""
        obj = await retrieval_tools_service.create(data)
        return retrieval_tools_service.to_schema(obj, schema_type=RetrievalTool)

    @get("/code/{code:str}")
    async def get_retrieval_tool_by_code(
        self, retrieval_tools_service: RetrievalToolsService, code: str
    ) -> RetrievalTool:
        """Get a Retrieval tool by its system_name."""
        obj = await retrieval_tools_service.get_one(system_name=code)
        return retrieval_tools_service.to_schema(obj, schema_type=RetrievalTool)

    @get("/{retrieval_tool_id:uuid}")
    async def get_retrieval_tool(
        self,
        retrieval_tools_service: RetrievalToolsService,
        retrieval_tool_id: UUID = Parameter(
            title="Retrieval Tool ID",
            description="The Retrieval tool to retrieve.",
        ),
    ) -> RetrievalTool:
        """Get a Retrieval tool by its ID."""
        obj = await retrieval_tools_service.get(retrieval_tool_id)
        return retrieval_tools_service.to_schema(obj, schema_type=RetrievalTool)

    @patch("/{retrieval_tool_id:uuid}")
    async def update_retrieval_tool(
        self,
        retrieval_tools_service: RetrievalToolsService,
        data: RetrievalToolUpdate,
        retrieval_tool_id: UUID = Parameter(
            title="Retrieval Tool ID",
            description="The Retrieval tool to update.",
        ),
    ) -> RetrievalTool:
        """Update a Retrieval tool."""
        obj = await retrieval_tools_service.update(
            data, item_id=retrieval_tool_id, auto_commit=True
        )
        return retrieval_tools_service.to_schema(obj, schema_type=RetrievalTool)

    @delete("/{retrieval_tool_id:uuid}")
    async def delete_retrieval_tool(
        self,
        retrieval_tools_service: RetrievalToolsService,
        retrieval_tool_id: UUID = Parameter(
            title="Retrieval Tool ID",
            description="The Retrieval tool to delete.",
        ),
    ) -> None:
        """Delete a Retrieval tool from the system."""
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
