from litestar import post
from litestar.connection import Request
from litestar.status_codes import HTTP_200_OK

from services.flow_retrieval_execute import flow_retrieval_execute
from services.flow_retrieval_test import RetrievalToolTestResult, flow_retrieval_test
from services.observability import observability_context, observe
from validation.retrieval_tools import (
    RetrievalToolExecute,
    RetrievalToolsConfig,
    RetrievalToolTest,
)

from .create_entity_controller import create_entity_controller

RetrievalToolsBaseController = create_entity_controller(
    path_param="/retrieval_tools",
    collection_name="retrieval_tools",
    model=RetrievalToolsConfig,
)


class RetrievalToolsController(RetrievalToolsBaseController):
    tags = ["retrieval_tools"]

    @observe(name="Previewing Retrieval Tool", channel="preview")
    @post("/test", status_code=HTTP_200_OK)
    async def retrieval_tool_test(
        self, data: RetrievalToolTest
    ) -> RetrievalToolTestResult:
        observability_context.update_current_trace(
            name=data.name, type="retrieval-tool"
        )

        result = await flow_retrieval_test(data)

        return result

    # This is duplicated in user routes. TODO - delete after verifying it's not used in admin panel
    @observe(name="Executing Retrieval Tool", channel="production")
    @post("/execute", status_code=HTTP_200_OK)
    async def retrieval_tool_execute(
        self,
        data: RetrievalToolExecute,
        request: Request,  # do not remove this, it is used to get x-attributes in observe decorator
    ) -> RetrievalToolTestResult:
        observability_context.update_current_trace(
            name=data.name, type="retrieval-tool"
        )

        result = await flow_retrieval_execute(data)

        return result


class RetrievalToolsControllerDeprecated(RetrievalToolsController):
    path = "retrieval"
    tags = ["retrieval_deprecated"]
