from services.agents.models import (
    AgentConversationClassification,
    AgentConversationMessageAssistant,
    AgentConversationMessageUser,
    AgentConversationRun,
    AgentConversationRunStepClassification,
    AgentConversationRunStepTopicCompletion,
    AgentConversationSelectedTopic,
    AgentConversationTopicCompletion,
    ConversationIntent,
)
from services.agents.services import (
    generate_completion_messages,
)
from utils.datetime_utils import utc_now


def test_no_topic_processing():
    messages = [
        AgentConversationMessageUser(id="1", content="Hi!"),
        AgentConversationMessageAssistant(
            id="2",
            content="Hello, how can I help you?",
            run=AgentConversationRun(
                steps=[
                    AgentConversationRunStepClassification(
                        started_at=utc_now(),
                        details=AgentConversationClassification(
                            intent=ConversationIntent.GREETING,
                            reason="",
                            assistant_message="Hello, how can I help you?",
                        ),
                    ),
                ],
            ),
        ),
    ]

    result = generate_completion_messages(messages=messages)

    assert len(result) == 2

    assert result[0].get("role") == "user"
    assert result[0].get("content") == "Hi!"
    assert result[1].get("role") == "assistant"
    assert result[1].get("content") == "Hello, how can I help you?"


def test_topic_processing_no_action_calls():
    messages = [
        AgentConversationMessageUser(id="1", content="Hello, I want to unsubsribe."),
        AgentConversationMessageAssistant(
            id="2",
            content="Test assistant message",
            run=AgentConversationRun(
                steps=[
                    AgentConversationRunStepClassification(
                        started_at=utc_now(),
                        details=AgentConversationClassification(
                            intent=ConversationIntent.TOPIC,
                            reason="",
                            topic="TOPIC_1",
                        ),
                    ),
                    AgentConversationRunStepTopicCompletion(
                        started_at=utc_now(),
                        details=AgentConversationTopicCompletion(
                            topic=AgentConversationSelectedTopic(
                                system_name="SUBSCRIPTIONS",
                                name="",
                                description="",
                            ),
                            assistant_message="Sure, please name your subscription id?",
                        ),
                    ),
                ],
            ),
        ),
    ]

    result = generate_completion_messages(messages=messages)

    assert len(result) == 2

    assert result[0].get("role") == "user"
    assert result[0].get("content") == "Hello, I want to unsubsribe."
    assert result[1].get("role") == "assistant"
    assert result[1].get("content") == "Sure, please name your subscription id?"


def test_assistant_message_without_run():
    messages = [
        AgentConversationMessageAssistant(
            id="1",
            content="Hello, how can I assist you today?",
        ),
        AgentConversationMessageUser(id="1", content="Hello, I want to unsubsribe."),
    ]

    result = generate_completion_messages(messages=messages)

    assert len(result) == 2

    assert result[0].get("role") == "assistant"
    assert result[0].get("content") == "Hello, how can I assist you today?"
    assert result[1].get("role") == "user"
    assert result[1].get("content") == "Hello, I want to unsubsribe."
