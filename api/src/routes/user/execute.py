from typing import Annotated

from litestar import Controller, post
from litestar.connection import Request
from litestar.params import Body
from litestar.status_codes import HTTP_200_OK

from api.tags import TagNames
from prompt_templates.prompt_templates import get_prompt_template_by_system_name_flat
from services.flow_retrieval_execute import flow_retrieval_execute
from services.flow_retrieval_test import RetrievalToolTestResult
from services.observability import (
    observability_context,
    observe,
)
from services.prompt_templates import execute_prompt_template
from services.prompt_templates.models import (
    PromptTemplateExecuteRequest,
    PromptTemplateExecutionResponse,
)
from services.rag_tools import execute_rag_tool
from services.rag_tools.models import RagToolTestResult
from services.rag_tools.services import get_rag_by_system_name_flat
from validation.rag_tools import RagToolExecute
from validation.retrieval_tools import RetrievalToolExecute

RagToolExecuteResponse = RagToolTestResult


# TODO - check if there is extra data in responses, not needed to be exposed to user
class UserExecuteController(Controller):
    path = "/execute"
    tags = [TagNames.UserExecute]

    @observe(
        name="Executing Prompt Template",
        channel="production",
        source="Runtime API",
    )
    @post(
        "/prompt_template",
        status_code=HTTP_200_OK,
        summary="Execute a prompt template",
        description="Executes a predefined prompt template using the provided system name and user message content.",
    )
    async def prompt_template_execute(
        self,
        data: Annotated[PromptTemplateExecuteRequest, Body()],
        user_id: str | None,
        request: Request,  # do not remove this, it is used to get the consumer name and type in decorator
    ) -> PromptTemplateExecutionResponse:
        prompt_template_config = await get_prompt_template_by_system_name_flat(
            data.system_name,
        )

        observability_context.update_current_baggage(user_id=user_id)

        observability_context.update_current_trace(
            name=prompt_template_config.get("name"), type="prompt-template"
        )

        result = await execute_prompt_template(
            system_name_or_config=prompt_template_config,
            template_values=data.system_message_values,
            template_additional_messages=[
                {
                    "role": "user",
                    "content": data.user_message,
                },
            ],
        )

        return result

    @observe(name="Executing RAG Tool", channel="production")
    @post(
        "/rag_tool",
        status_code=HTTP_200_OK,
        summary="Execute a RAG tool",
        description="Executes a Retrieval-Augmented Generation (RAG) tool using the provided system name and user message.",
    )
    async def rag_tool_execute(
        self,
        data: RagToolExecute,
        user_id: str | None,
        request: Request,  # do not remove this, it is used to get x-attributes in observe decorator
    ) -> RagToolExecuteResponse:
        rag_tool_config = await get_rag_by_system_name_flat(data.system_name)

        observability_context.update_current_baggage(
            source=request.headers.get("x-source") or "Runtime API",
            consumer_type=request.headers.get("x-consumer-type") or "rag",
            consumer_name=(
                request.headers.get("x-consumer-name")
                or rag_tool_config.get("system_name")
            ),
            user_id=user_id,
        )

        observability_context.update_current_trace(
            name=rag_tool_config.get("name"), type="rag", user_id=user_id
        )

        return await execute_rag_tool(
            system_name_or_config=rag_tool_config,
            user_message=data.user_message,
            metadata_filter=data.metadata_filter,
        )

    @observe(name="Executing Retrieval Tool", channel="production")
    @post(
        "/retrieval_tool",
        status_code=HTTP_200_OK,
        summary="Execute a Retrieval Tool",
        description="Executes a Retrieval Tool using the provided configuration and returns the result.",
    )
    async def retrieval_tool_execute(
        self,
        data: RetrievalToolExecute,
        user_id: str | None,
        request: Request,  # do not remove this, it is used to get x-attributes in observe decorator
    ) -> RetrievalToolTestResult:
        observability_context.update_current_baggage(
            source=request.headers.get("x-source") or "Runtime API",
            consumer_type=request.headers.get("x-consumer-type") or "retrieval",
            consumer_name=(request.headers.get("x-consumer-name") or data.system_name),
            user_id=user_id,
        )

        observability_context.update_current_trace(
            name=data.name, type="retrieval-tool"
        )

        return await flow_retrieval_execute(data)
