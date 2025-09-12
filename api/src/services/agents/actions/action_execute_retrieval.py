from dataclasses import asdict

from langchain.schema import Document

from services.agents.models import AgentActionCallResponse
from services.flow_retrieval_execute import flow_retrieval_execute
from services.flow_retrieval_test import RetrievalToolTestResult
from services.get_chat_completion_answer import get_document_context
from services.observability import observability_context, observe
from services.observability.models import SpanType
from validation.retrieval_tools import RetrievalToolExecute


@observe(
    name="Call Retrieval",
    description="Retrieve data using Retrieval tool. The agent determines what query to execute against the Retrieval tool.",
    type=SpanType.TOOL,
)
async def action_execute_retrieval(
    tool_system_name: str,
    arguments: dict,
    variables: dict[str, str] | None = None,
) -> AgentActionCallResponse:
    query = arguments.get("query")

    assert query, "Cannot call Retrieval Tool - user's query is missing"

    observability_context.update_current_span(
        input={"Retrieval tool system name": tool_system_name, "Query": query},
    )

    tool_execute_result: RetrievalToolTestResult = await flow_retrieval_execute(
        RetrievalToolExecute(system_name=tool_system_name, user_message=query),
    )

    results_stringified = "\n\n".join(
        get_document_context(
            Document(
                page_content=result_item.content,
                metadata=result_item.metadata,
            ),
        )
        for result_item in tool_execute_result.results
    )

    result = AgentActionCallResponse(
        content=results_stringified,
        verbose_details=asdict(tool_execute_result),
    )

    return result
