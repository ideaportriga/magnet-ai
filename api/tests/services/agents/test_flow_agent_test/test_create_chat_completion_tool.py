from http import HTTPMethod

import pytest

from services.agents.models import AgentAction, AgentActionType
from services.agents.services import create_chat_completion_tool
from services.api_tools.types import ApiTool, ApiToolParameters, ApiToolVariantValue
from services.entities.types import EntityVariant


@pytest.mark.parametrize(
    "action_type, expected_parameters",
    [
        (
            AgentActionType.RAG,
            {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "User's query"},
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        ),
        (
            AgentActionType.RETRIEVAL,
            {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "User's query"},
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        ),
        (
            AgentActionType.PROMPT_TEMPLATE,
            {
                "type": "object",
                "properties": {
                    "userMessage": {"type": "string", "description": "User message"},
                },
                "required": ["userMessage"],
                "additionalProperties": False,
            },
        ),
    ],
)
def test_create_chat_completion_tool(action_type, expected_parameters):
    function_name = "test_function"
    function_description = "Test function description"

    action = AgentAction(
        name="Test Action",
        system_name="test_action",
        description="Test action description",
        display_name="Test Action",
        display_description="Test action description",
        type=action_type,
        tool_system_name="test_tool",
        function_name=function_name,
        function_description=function_description,
    )

    result = create_chat_completion_tool(action, api_tools_by_system_name={})

    assert result["type"] == "function"
    assert result["function"]["name"] == function_name
    assert result["function"].get("description") == function_description
    assert result["function"].get("parameters") == expected_parameters


@pytest.mark.parametrize(
    "action_type, expected_parameters",
    [
        (
            AgentActionType.RAG,
            {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "User's query"},
                    "actionMessage": {
                        "type": "string",
                        "description": "Action message LLM description value",
                    },
                },
                "required": ["query", "actionMessage"],
                "additionalProperties": False,
            },
        ),
        (
            AgentActionType.RETRIEVAL,
            {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "User's query"},
                    "actionMessage": {
                        "type": "string",
                        "description": "Action message LLM description value",
                    },
                },
                "required": ["query", "actionMessage"],
                "additionalProperties": False,
            },
        ),
        (
            AgentActionType.PROMPT_TEMPLATE,
            {
                "type": "object",
                "properties": {
                    "userMessage": {"type": "string", "description": "User message"},
                    "actionMessage": {
                        "type": "string",
                        "description": "Action message LLM description value",
                    },
                },
                "required": ["userMessage", "actionMessage"],
                "additionalProperties": False,
            },
        ),
    ],
)
def test_create_chat_completion_tool_with_confirmation(
    action_type, expected_parameters,
):
    function_name = "test_function"
    function_description = "Test function description"
    action_message_llm_description = "Action message LLM description value"

    action = AgentAction(
        name="Test Action",
        system_name="test_action",
        description="Test action description",
        display_name="Test Action",
        display_description="Test action description",
        type=action_type,
        tool_system_name="test_tool",
        function_name=function_name,
        function_description=function_description,
        requires_confirmation=True,
        action_message_llm_description=action_message_llm_description,
    )

    result = create_chat_completion_tool(action, api_tools_by_system_name={})

    assert result["type"] == "function"
    assert result["function"]["name"] == function_name
    assert result["function"].get("description") == function_description
    assert result["function"].get("parameters") == expected_parameters


def test_create_chat_completion_tool_api_action():
    function_name = "get_contact_info"
    function_description = "Get contact info for the contact by id"
    tool_system_name = "get_contact_info_tool"

    action = AgentAction(
        name="Test API Action",
        system_name="test_api_action",
        description="Test API action description",
        display_name="Test API Action",
        display_description="Test API action description",
        type=AgentActionType.API,
        tool_system_name=tool_system_name,
        function_name=function_name,
        function_description=function_description,
    )

    api_tool_input_parameters_input = {
        "type": "object",
        "properties": {
            "requestBody": {
                "type": "string",
                "description": "...",
            },
        },
        "required": ["requestBody"],
        "additionalProperties": False,
    }

    mock_api_tool = ApiTool(
        name="Test API Tool",
        system_name="test_tool",
        api_provider="Provider1",
        path="/test",
        method=HTTPMethod.POST,
        active_variant="v1",
        original_parameters=ApiToolParameters(
            input=api_tool_input_parameters_input, output={},
        ),
        original_operation_definition={},
        variants=[
            EntityVariant[ApiToolVariantValue](
                variant="v1",
                value=ApiToolVariantValue(
                    parameters=ApiToolParameters(
                        input=api_tool_input_parameters_input, output={},
                    ),
                ),
            ),
        ],
    )

    api_tools_by_system_name = {tool_system_name: mock_api_tool}

    result = create_chat_completion_tool(action, api_tools_by_system_name)

    assert result["type"] == "function"
    assert result["function"]["name"] == function_name
    assert result["function"].get("description") == function_description
    assert result["function"].get("parameters") == api_tool_input_parameters_input


def test_create_chat_completion_tool_api_action_with_confirmation():
    action_message_llm_description = "Get contact info for the contact 1"
    function_name = "get_contact_info"
    function_description = "Get contact info for the contact by id"
    tool_system_name = "get_contact_info_tool"

    action = AgentAction(
        name="Test API Action",
        system_name="test_api_action",
        description="Test API action description",
        display_name="Test API Action",
        display_description="Test API action description",
        type=AgentActionType.API,
        tool_system_name=tool_system_name,
        function_name=function_name,
        function_description=function_description,
        requires_confirmation=True,
        action_message_llm_description=action_message_llm_description,
    )

    api_tool_input_parameters_input = {
        "type": "object",
        "properties": {
            "requestBody": {
                "type": "string",
                "description": "...",
            },
        },
        "required": ["requestBody"],
        "additionalProperties": False,
    }

    mock_api_tool = ApiTool(
        name="Test API Tool",
        system_name=tool_system_name,
        api_provider="Provider1",
        path="/test",
        method=HTTPMethod.POST,
        active_variant="v1",
        original_parameters=ApiToolParameters(
            input=api_tool_input_parameters_input, output={},
        ),
        original_operation_definition={},
        variants=[
            EntityVariant[ApiToolVariantValue](
                variant="v1",
                value=ApiToolVariantValue(
                    parameters=ApiToolParameters(
                        input=api_tool_input_parameters_input, output={},
                    ),
                ),
            ),
        ],
    )

    api_tools_by_system_name = {tool_system_name: mock_api_tool}

    result = create_chat_completion_tool(action, api_tools_by_system_name)

    assert result["type"] == "function"
    assert result["function"]["name"] == function_name
    assert result["function"].get("description") == function_description
    assert "parameters" in result["function"]
    assert result["function"]["parameters"] == api_tool_input_parameters_input
