import pytest
from pytest_mock import MockerFixture

from services.agents.models import (
    AgentConversationClassification,
    AgentConversationMessage,
    AgentConversationMessageUser,
    AgentTopic,
    ConversationIntent,
)
from services.agents.services import (
    classify_conversation,
)

pytest.skip(allow_module_level=True, reason="TODO - Skip/mock @observe decorator")


def test_executes_prompt_template_intent_topic(mocker: MockerFixture):
    topics = [
        AgentTopic(
            name="Topic 1",
            system_name="topic_1",
            description="First topic description",
            instructions="",
            actions=[],
        ),
        AgentTopic(
            name="Topic 2",
            system_name="topic_2",
            description="Second topic description",
            instructions="",
            actions=[],
        ),
    ]

    messages: list[AgentConversationMessage] = [
        AgentConversationMessageUser(
            id="1",
            content="Test message",
        ),
    ]
    prompt_template = "CLASSIFICATION_PROMPT_TEMPLATE"
    mock_prompt_template_execute = mocker.patch(
        "services.agents.services.execute_prompt_template",
    )
    mock_prompt_template_execute.return_value.content = (
        '{"intent": "topic", "topic": "topic_1", "reason": "test reason"}'
    )

    result = classify_conversation(
        prompt_template=prompt_template, messages=messages, topics=topics,
    )

    expected_completion_messsage = {
        "role": "user",
        "content": '[\n  {\n    "role": "user",\n    "content": "Test message"\n  }\n]',
    }

    expected_prompt_template_values = {
        "TOPIC_DEFINITIONS": [
            {
                "system_name": "topic_1",
                "name": "Topic 1",
                "description": "First topic description",
            },
            {
                "system_name": "topic_2",
                "name": "Topic 2",
                "description": "Second topic description",
            },
        ],
        "TOPIC_SYSTEM_NAMES": ["topic_1", "topic_2"],
    }
    expected_result = AgentConversationClassification(
        intent=ConversationIntent.TOPIC,
        topic="topic_1",
        reason="test reason",
    )

    mock_prompt_template_execute.assert_called_once()
    _, mock_prompt_template_execute_call_kwargs = mock_prompt_template_execute.call_args
    assert (
        mock_prompt_template_execute_call_kwargs["system_name_or_config"]
        == prompt_template
    )
    assert mock_prompt_template_execute_call_kwargs["template_additional_messages"] == [
        expected_completion_messsage,
    ]
    assert (
        mock_prompt_template_execute_call_kwargs["template_values"]
        == expected_prompt_template_values
    )
    assert result == expected_result


def test_executes_prompt_template_intent_no_topics(mocker: MockerFixture):
    topics = []

    messages: list[AgentConversationMessage] = [
        AgentConversationMessageUser(id="1", content="Test message"),
    ]
    prompt_template = "CLASSIFICATION_PROMPT_TEMPLATE"
    mock_prompt_template_execute = mocker.patch(
        "services.agents.services.execute_prompt_template",
    )
    mock_prompt_template_execute.return_value.content = '{"intent": "off_topic", "assistant_message": "Assistant message", "reason": "test reason"}'

    result = classify_conversation(
        prompt_template=prompt_template, messages=messages, topics=topics,
    )

    expected_completion_messsage = {
        "role": "user",
        "content": '[\n  {\n    "role": "user",\n    "content": "Test message"\n  }\n]',
    }

    expected_prompt_template_values = {
        "TOPIC_DEFINITIONS": "No topics.",
        "TOPIC_SYSTEM_NAMES": "",
    }
    expected_result = AgentConversationClassification(
        intent=ConversationIntent.OFF_TOPIC,
        assistant_message="Assistant message",
        reason="test reason",
    )

    mock_prompt_template_execute.assert_called_once()
    _, mock_prompt_template_execute_call_kwargs = mock_prompt_template_execute.call_args

    assert (
        mock_prompt_template_execute_call_kwargs["system_name_or_config"]
        == prompt_template
    )

    assert mock_prompt_template_execute_call_kwargs["template_additional_messages"] == [
        expected_completion_messsage,
    ]
    assert (
        mock_prompt_template_execute_call_kwargs["template_values"]
        == expected_prompt_template_values
    )
    assert result == expected_result
