from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from advanced_alchemy.extensions.litestar import filters, providers, service
from litestar import Controller, delete, get, patch, post
from litestar.params import Dependency, Parameter
from advanced_alchemy.filters import LimitOffset

from core.config.constants import DEFAULT_PAGINATION_SIZE
from core.domain.rag_tools.schemas import RagTool, RagToolCreate, RagToolUpdate
from core.domain.rag_tools.service import RagToolsService

if TYPE_CHECKING:
    pass


class RagToolsController(Controller):
    """RAG Tools CRUD"""

    path = "/sql_rag_tools"
    tags = ["sql_RagTools"]

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
