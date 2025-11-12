from __future__ import annotations

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
from services.observability import observability_context, observe
from services.rag_tools import execute_rag_tool
from services.rag_tools.models import RagToolTestResult
from services.rag_tools.services import get_rag_by_system_name_flat
from services.utils.metadata_filtering import metadata_filter_to_filter_object
from validation.rag_tools import RagToolExecute, RagToolTest

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
        },
    )

    @get()
    async def list_rag_tools(
        self,
        rag_tools_service: RagToolsService,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
    ) -> service.OffsetPagination[RagTool]:
        """List RAG tools with pagination and filtering."""
        results, total = await rag_tools_service.list_and_count(*filters)
        return rag_tools_service.to_schema(
            results, total, filters=filters, schema_type=RagTool
        )

    @post()
    async def create_rag_tool(
        self, rag_tools_service: RagToolsService, data: RagToolCreate
    ) -> RagTool:
        """Create a new RAG tool."""
        obj = await rag_tools_service.create(data)
        return rag_tools_service.to_schema(obj, schema_type=RagTool)

    @get("/code/{code:str}")
    async def get_rag_tool_by_code(
        self, rag_tools_service: RagToolsService, code: str
    ) -> RagTool:
        """Get a RAG tool by its system_name."""
        obj = await rag_tools_service.get_one(system_name=code)
        return rag_tools_service.to_schema(obj, schema_type=RagTool)

    @get("/{rag_tool_id:uuid}")
    async def get_rag_tool(
        self,
        rag_tools_service: RagToolsService,
        rag_tool_id: UUID = Parameter(
            title="RAG Tool ID",
            description="The RAG tool to retrieve.",
        ),
    ) -> RagTool:
        """Get a RAG tool by its ID."""
        obj = await rag_tools_service.get(rag_tool_id)
        return rag_tools_service.to_schema(obj, schema_type=RagTool)

    @patch("/{rag_tool_id:uuid}")
    async def update_rag_tool(
        self,
        rag_tools_service: RagToolsService,
        data: RagToolUpdate,
        rag_tool_id: UUID = Parameter(
            title="RAG Tool ID",
            description="The RAG tool to update.",
        ),
    ) -> RagTool:
        """Update a RAG tool."""
        obj = await rag_tools_service.update(
            data, item_id=rag_tool_id, auto_commit=True
        )
        return rag_tools_service.to_schema(obj, schema_type=RagTool)

    @delete("/{rag_tool_id:uuid}")
    async def delete_rag_tool(
        self,
        rag_tools_service: RagToolsService,
        rag_tool_id: UUID = Parameter(
            title="RAG Tool ID",
            description="The RAG tool to delete.",
        ),
    ) -> None:
        """Delete a RAG tool from the system."""
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
            metadata_filter=metadata_filter_to_filter_object(data.metadata_filter),
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
