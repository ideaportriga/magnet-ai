import pytest
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
    Function,
)
from pytest_mock import MockerFixture

from services.agents.models import (
    AgentAction,
    AgentActionCallResponse,
    AgentActionType,
    AgentConversationMessage,
    AgentConversationMessageUser,
    AgentConversationRunStepTopicActionCall,
    AgentConversationRunStepTopicCompletion,
    AgentTopic,
)
from services.agents.services import (
    execute_topic,
)

pytest.skip(allow_module_level=True, reason="TODO - Skip/mock @observe decorator")


def test_no_tool_calls(mocker: MockerFixture):
    """Tests that execute_topic correctly processes a topic with actions and returns expected result"""
    messages: list[AgentConversationMessage] = [
        AgentConversationMessageUser(id="1", content="Test message"),
    ]

    topic = AgentTopic(
        name="Test Topic",
        system_name="test_topic",
        description="Test topic description",
        actions=[
            AgentAction(
                name="Test Action",
                system_name="test_action",
                description="Test action description",
                type=AgentActionType.RAG,
                display_name="Test Action Display",
                display_description="Test action display description",
                tool_system_name="test_tool",
                function_name="test_function",
                function_description="Test function description",
            ),
        ],
    )

    mock_chat_completion = mocker.patch(
        "services.agents.services.get_prompt_template_by_system_name_flat",
        return_value={},
    )
    mock_chat_completion = mocker.patch(
        "services.agents.services.create_chat_completion_from_prompt_template",
        return_value=[
            mocker.Mock(
                choices=[
                    mocker.Mock(
                        message=mocker.Mock(
                            content="Test assistant response",
                            tool_calls=None,
                        ),
                    ),
                ],
            ),
        ],
    )

    result = execute_topic(
        topic=topic,
        messages=messages,
        prompt_template="test_prompt_template",
    )

    mock_chat_completion.assert_called_once()
    assert result.content == "Test assistant response"
    assert len(result.steps) == 1

    topic_completion_step = result.steps[0]
    assert isinstance(topic_completion_step, AgentConversationRunStepTopicCompletion)
    assert topic_completion_step.details.assistant_message == "Test assistant response"
    assert topic_completion_step.details.topic.system_name == topic.system_name
    assert topic_completion_step.details.topic.name == topic.name
    assert topic_completion_step.details.topic.description == topic.description
    assert not topic_completion_step.details.action_call_requests


def test_tool_calls(mocker: MockerFixture):
    topic = AgentTopic(
        name="Test Topic",
        system_name="test_topic",
        description="Test topic description",
        actions=[
            AgentAction(
                name="Test Action",
                system_name="test_action",
                description="Test action description",
                type=AgentActionType.RAG,
                display_name="Test Action Display",
                display_description="Test action display description",
                tool_system_name="test_tool",
                function_name="test_function",
                function_description="Test function description",
            ),
        ],
    )
    messages: list[AgentConversationMessage] = [
        AgentConversationMessageUser(id="1", content="Test message"),
    ]
    prompt_template = "test_prompt_template"
    prompt_template_config_mocked = {"system_name": prompt_template}

    chat_completion_with_function_calls_mocked = mocker.Mock(
        choices=[
            mocker.Mock(
                message=mocker.Mock(
                    role="assistant",
                    content=None,
                    tool_calls=[
                        ChatCompletionMessageToolCall(
                            id="function_call_1",
                            type="function",
                            function=Function(
                                name="test_function",
                                arguments="""{"query": "Test user query"}""",
                            ),
                        ),
                    ],
                ),
            ),
        ],
    )
    chat_completion_with_content_mocked = mocker.Mock(
        choices=[
            mocker.Mock(
                message=mocker.Mock(
                    role="assistant",
                    content="Test assistant response content",
                    tool_calls=None,
                ),
            ),
        ],
    )

    mock_get_prompt_template = mocker.patch(
        "services.agents.services.get_prompt_template_by_system_name_flat",
        return_value=prompt_template_config_mocked,
    )

    mock_create_chat_completion = mocker.patch(
        "services.agents.services.create_chat_completion_from_prompt_template",
        side_effect=[
            (chat_completion_with_function_calls_mocked, []),
            (chat_completion_with_content_mocked, []),
        ],
    )

    mock_execute_agent_action = mocker.patch(
        "services.agents.services.execute_agent_action",
        return_value=AgentActionCallResponse(
            content="Action response",
        ),
    )

    result = execute_topic(
        topic=topic,
        messages=messages,
        prompt_template=prompt_template,
    )

    mock_get_prompt_template.assert_called_once_with(
        prompt_template_system_name=prompt_template,
    )
    mock_execute_agent_action.assert_called_once()
    assert mock_create_chat_completion.call_count == 2

    assert result.content == "Test assistant response content"
    assert len(result.steps) == 3

    assert isinstance(result.steps[0], AgentConversationRunStepTopicCompletion)
    assert isinstance(result.steps[1], AgentConversationRunStepTopicActionCall)
    assert isinstance(result.steps[2], AgentConversationRunStepTopicCompletion)


def test_max_iteration_count_reached(mocker: MockerFixture):
    topic = AgentTopic(
        name="Test Topic",
        system_name="test_topic",
        description="Test topic description",
        actions=[
            AgentAction(
                name="Test Action",
                system_name="test_action",
                description="Test action description",
                type=AgentActionType.RAG,
                display_name="Test Action Display",
                display_description="Test action display description",
                tool_system_name="test_tool",
                function_name="test_function",
                function_description="Test function description",
            ),
        ],
    )
    messages: list[AgentConversationMessage] = [
        AgentConversationMessageUser(id="1", content="Test message"),
    ]
    prompt_template = "test_prompt_template"
    prompt_template_config_mocked = {"system_name": prompt_template}

    chat_completion_with_function_calls_mocked = mocker.Mock(
        choices=[
            mocker.Mock(
                message=mocker.Mock(
                    role="assistant",
                    content=None,
                    tool_calls=[
                        ChatCompletionMessageToolCall(
                            id="function_call_1",
                            type="function",
                            function=Function(
                                name="test_function",
                                arguments="""{"query": "Test user query"}""",
                            ),
                        ),
                    ],
                ),
            ),
        ],
    )

    mock_get_prompt_template = mocker.patch(
        "services.agents.services.get_prompt_template_by_system_name_flat",
        return_value=prompt_template_config_mocked,
    )

    mock_create_chat_completion = mocker.patch(
        "services.agents.services.create_chat_completion_from_prompt_template",
        return_value=(
            chat_completion_with_function_calls_mocked,
            [],
        ),
    )

    mock_execute_agent_action = mocker.patch(
        "services.agents.services.execute_agent_action",
        return_value=AgentActionCallResponse(
            content="Action response",
        ),
    )

    with pytest.raises(ValueError):
        execute_topic(topic=topic, messages=messages, prompt_template=prompt_template)

    mock_get_prompt_template.assert_called_once()
    assert mock_execute_agent_action.call_count == 5
    assert mock_create_chat_completion.call_count == 5
