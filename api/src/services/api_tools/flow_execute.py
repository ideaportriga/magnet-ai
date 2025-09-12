from services.api_tools.flow_test import api_tool_test
from services.api_tools.types import (
    ApiToolBase,
    ApiToolExecute,
    ApiToolExecuteResult,
    ApiToolTest,
)
from stores import get_db_client

client = get_db_client()


async def api_tool_execute(params: ApiToolExecute) -> ApiToolExecuteResult:
    api_tool_config = await get_api_tool_config(params.system_name)

    test_params = ApiToolTest(
        api_tool_config=api_tool_config,
        input_params=params.input_params,
        variables=params.variables,
    )

    result = await api_tool_test(test_params)

    return result


async def get_api_tool_config(system_name: str) -> ApiToolBase:
    document = await client.get_collection("api_tools").find_one(
        {"system_name": system_name}
    )

    assert document, "API Tool not found"

    api_tool = ApiToolBase(**document)

    return api_tool
