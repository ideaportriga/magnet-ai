from http import HTTPMethod

from pytest_mock import MockerFixture

from services.agents.models import (
    AgentAction,
    AgentActionType,
)
from services.agents.services import (
    create_chat_completion_tools,
)
from services.api_tools.types import ApiTool, ApiToolParameters, ApiToolVariantValue
from services.entities.types import EntityVariant


def test_create_chat_completion_tools(mocker: MockerFixture):
    actions = [
        AgentAction(
            name="API Action",
            system_name="api_action",
            description="API action description",
            display_name="API Action",
            display_description="API action description",
            type=AgentActionType.API,
            tool_system_name="test_api_tool",
            function_name="test_api_function",
            function_description="Test API function description",
        ),
        AgentAction(
            name="RAG Action",
            system_name="rag_action",
            description="RAG action description",
            type=AgentActionType.RAG,
            display_name="RAG Action",
            display_description="RAG action description",
            tool_system_name="test_rag_tool",
            function_name="test_rag_function",
            function_description="Test RAG function description",
        ),
        AgentAction(
            name="Prompt Template Action",
            system_name="prompt_template_action",
            description="Prompt Template action description",
            type=AgentActionType.PROMPT_TEMPLATE,
            display_name="Prompt Template Action",
            display_description="Prompt Template action description",
            tool_system_name="test_prompt_template_tool",
            function_name="test_prompt_template_function",
            function_description="Test Prompt Template function description",
        ),
    ]

    api_tool_input_parameters = {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City and country e.g. Bogotá, Colombia",
            },
        },
        "required": ["location"],
        "additionalProperties": False,
    }

    mock_api_tool = ApiTool(
        name="Test API Tool",
        system_name="test_api_tool",
        api_provider="Provider1",
        path="/test",
        method=HTTPMethod.POST,
        active_variant="v1",
        original_parameters=ApiToolParameters(
            input=api_tool_input_parameters, output={},
        ),
        original_operation_definition={},
        variants=[
            EntityVariant[ApiToolVariantValue](
                variant="v1",
                value=ApiToolVariantValue(
                    parameters=ApiToolParameters(
                        input=api_tool_input_parameters, output={},
                    ),
                ),
            ),
        ],
    )

    mock_get_api_tools = mocker.patch(
        "services.agents.services.get_api_tools_by_system_name",
        return_value={"test_api_tool": mock_api_tool},
    )

    result = create_chat_completion_tools(actions)

    mock_get_api_tools.assert_called_once()
    assert len(result) == 3

    completion_tool_api = result[0]

    assert completion_tool_api["type"] == "function"
    assert completion_tool_api["function"]["name"] == "test_api_function"
    assert (
        completion_tool_api["function"].get("description", "")
        == "Test API function description"
    )
    assert (
        completion_tool_api["function"].get("parameters", {})
        == api_tool_input_parameters
    )

    completion_tool_rag = result[1]
    assert completion_tool_rag["type"] == "function"
    assert completion_tool_rag["function"]["name"] == "test_rag_function"
    assert (
        completion_tool_rag["function"].get("description", "")
        == "Test RAG function description"
    )
    assert completion_tool_rag["function"].get("parameters", {}) == {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "User's query"},
        },
        "required": ["query"],
        "additionalProperties": False,
    }

    completion_tool_prompt_template = result[2]
    assert completion_tool_prompt_template["type"] == "function"
    assert (
        completion_tool_prompt_template["function"]["name"]
        == "test_prompt_template_function"
    )
    assert (
        completion_tool_prompt_template["function"].get("description", "")
        == "Test Prompt Template function description"
    )
    assert completion_tool_prompt_template["function"].get("parameters", {}) == {
        "type": "object",
        "properties": {
            "userMessage": {"type": "string", "description": "User message"},
        },
        "required": ["userMessage"],
        "additionalProperties": False,
    }
