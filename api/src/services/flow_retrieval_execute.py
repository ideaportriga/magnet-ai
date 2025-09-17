import os

from services.flow_retrieval_test import RetrievalToolTestResult, flow_retrieval_test
from services.observability import observe
from services.retrieval_tools.services import get_retrieval_by_system_name_flat
from validation.retrieval_tools import RetrievalToolExecute, RetrievalToolTest

env = os.environ


@observe(name="Calling Retrieval Tool")
async def flow_retrieval_execute(
    input: RetrievalToolExecute,
) -> RetrievalToolTestResult:
    retrieval_tool_config = await get_retrieval_by_system_name_flat(input.system_name)

    if not retrieval_tool_config:
        raise ValueError("Retrieval tool with this system name not found")

    entity = RetrievalToolTest(
        user_message=input.user_message,
        metadata_filter=input.metadata_filter,
        **retrieval_tool_config,
    )
    return await flow_retrieval_test(entity)
