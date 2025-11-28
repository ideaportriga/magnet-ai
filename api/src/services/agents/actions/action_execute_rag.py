import json
from logging import getLogger

from services.agents.models import AgentActionCallResponse
from services.observability import observability_context, observe
from services.observability.models import SpanType
from services.rag_tools import execute_rag_tool
from services.rag_tools.models import RagToolTestResult
from type_defs.pagination import FilterObject

logger = getLogger(__name__)


@observe(
    name="Call RAG",
    description="Retrieve data using RAG tool. The agent determines what query to execute against the RAG tool.",
    type=SpanType.TOOL,
)
async def action_execute_rag(
    tool_system_name: str,
    arguments: dict,
    variables: dict[str, str] | None = None,
) -> AgentActionCallResponse:
    query = arguments.get("query")
    metadata_filter = arguments.get("metadata_filter")
    if metadata_filter:
        try:
            metadata_filter = FilterObject(json.loads(metadata_filter))
        except Exception as e:
            logger.error(f"Failed to parse metadata filter: {e}")
            metadata_filter = None

    assert query, "Cannot call RAG Tool - user's query is missing"

    observability_context.update_current_span(
        input={"RAG tool system name": tool_system_name, "Query": query},
    )

    try:
        rag_tool_execute_result: RagToolTestResult = await execute_rag_tool(
            system_name_or_config=tool_system_name,
            user_message=query,
            metadata_filter=metadata_filter,
        )
    except Exception as e:
        # Handle exceptions as appropriate for your application
        raise RuntimeError(f"Failed to execute RAG tool: {e}")

    answer = rag_tool_execute_result.answer

    result = AgentActionCallResponse(
        content=answer,
        verbose_details=rag_tool_execute_result.model_dump(),
    )

    return result
