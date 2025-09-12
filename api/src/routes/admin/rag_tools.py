from litestar import post
from litestar.connection import Request
from litestar.status_codes import HTTP_200_OK

from services.observability import observability_context, observe
from services.rag_tools import execute_rag_tool
from services.rag_tools.models import RagToolTestResult
from services.rag_tools.services import get_rag_by_system_name_flat
from validation.rag_tools import RagToolExecute, RagToolsConfig, RagToolTest

from .create_entity_controller import create_entity_controller

RagToolsBaseController = create_entity_controller(
    path_param="/rag_tools",
    collection_name="rag_tools",
    model=RagToolsConfig,
)


RagToolTestResponse = RagToolTestResult
RagToolExecuteResponse = RagToolTestResult


class RagToolsController(RagToolsBaseController):
    tags = ["rag_tools"]

    @observe(name="Previewing RAG Tool", channel="preview")
    @post("/test", status_code=HTTP_200_OK)
    async def test(self, data: RagToolTest, user_id: str) -> RagToolTestResponse:
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
            config_override=data,
            verbose=True,
        )

    # This is duplicated in user routes. TODO - delete after verifying it's not used in admin panel
    @observe(name="Executing RAG Tool", channel="production")
    @post("/execute", status_code=HTTP_200_OK)
    async def execute(
        self,
        data: RagToolExecute,
        user_id: str,
        request: Request,  # do not remove this, it is used to get x-attributes in observe decorator
    ) -> RagToolExecuteResponse:
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
