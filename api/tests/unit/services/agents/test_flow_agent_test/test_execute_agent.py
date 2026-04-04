import pytest
from pytest_mock import MockerFixture

from services.agents.models import (
    AgentActionCallConfirmation,
    AgentActionCallRequest,
    AgentActionCallResponse,
    AgentActionType,
    AgentConversationClassification,
    AgentConversationExecuteTopicResult,
    AgentConversationMessage,
    AgentConversationMessageAssistant,
    AgentConversationMessageRole,
    AgentConversationMessageUser,
    AgentConversationRun,
    AgentConversationRunStepClassification,
    AgentConversationRunStepTopicActionCall,
    AgentConversationRunStepTopicCompletion,
    AgentConversationSelectedTopic,
    AgentConversationTopicCompletion,
    AgentPromptTemplates,
    AgentTopic,
    AgentTopicActionCall,
    AgentVariantValue,
    ConversationIntent,
)
from services.agents.services import _execute_agent
from utils.datetime_utils import utc_now

# pytest.skip(allow_module_level=True, reason="TODO - Skip/mock @observe decorator")


@pytest.mark.parametrize(
    "intent",
    [
        (ConversationIntent.GREETING),
        (ConversationIntent.REQUEST_NOT_CLEAR),
        (ConversationIntent.OFF_TOPIC),
    ],
)
def test_no_topic(mocker: MockerFixture, intent):
    """Tests that when intent is not ConversationIntent.TOPIC:
    - Topic execution is skipped
    - Assistant message is generated based on intent and conversation messages
    """
    mock_execute_topic = mocker.patch("services.agents.services.execute_topic")
    assistant_message = "Generated assistant message"
    reason = "Generated reason"
    messages: list[AgentConversationMessage] = [
        AgentConversationMessageUser(id="1", content="User's message"),
    ]

    mock_classify = mocker.patch("services.agents.services.classify_conversation")
    mock_classify.return_value = AgentConversationClassification(
        intent=intent,
        assistant_message=assistant_message,
        reason=reason,
    )

    agent_config = AgentVariantValue(
        topics=[],
        prompt_templates=AgentPromptTemplates(
            classification="agent_classification",
            topic_processing="agent_system",
        ),
    )

    result = _execute_agent(config_override=agent_config, messages=messages)

    mock_execute_topic.assert_not_called()

    assert result.role == AgentConversationMessageRole.ASSISTANT
    assert result.content == assistant_message
    assert result.run
    assert len(result.run.steps) == 1

    classification_step = result.run.steps[0]
    assert isinstance(classification_step, AgentConversationRunStepClassification)
    assert classification_step.details.intent == intent
    assert classification_step.details.reason == reason


def test_topic(mocker: MockerFixture):
    """Tests that when intent is ConversationIntent.TOPIC:
    - Topic execution is called with correct parameters
    - Result contains topic execution data
    """
    prompt_template_topic_processing = "topic_processing"
    topic_system_name = "test_topic"
    topic_name = "Test Topic"
    topic_description = "Test Topic Description"
    topic = AgentTopic(
        name=topic_name,
        system_name=topic_system_name,
        description=topic_description,
        instructions="Topic instructions",
        actions=[],
    )

    classification_step = AgentConversationRunStepClassification(
        started_at=utc_now(),
        details=AgentConversationClassification(
            intent=ConversationIntent.TOPIC,
            topic=topic_system_name,
            reason="Classification reason",
        ),
    )

    assistant_message = "Generated assistant message"
    topic_completion_step = AgentConversationRunStepTopicCompletion(
        started_at=utc_now(),
        details=AgentConversationTopicCompletion(
            topic=AgentConversationSelectedTopic(
                name=topic_name,
                system_name=topic_system_name,
                description=topic_description,
            ),
            assistant_message=assistant_message,
            action_call_requests=[],
        ),
    )

    messages: list[AgentConversationMessage] = [
        AgentConversationMessageUser(id="1", content="User's message"),
    ]

    reason = "Topic related reason"
    mock_classify = mocker.patch("services.agents.services.classify_conversation")
    mock_classify.return_value = AgentConversationClassification(
        intent=ConversationIntent.TOPIC,
        topic=topic_system_name,
        reason=reason,
    )

    mocked_execute_topic_steps = [classification_step, topic_completion_step]
    mock_execute_topic = mocker.patch("services.agents.services.execute_topic")
    mock_execute_topic.return_value = AgentConversationExecuteTopicResult(
        content=assistant_message,
        steps=mocked_execute_topic_steps,
    )

    agent_config = AgentVariantValue(
        topics=[topic],
        prompt_templates=AgentPromptTemplates(
            classification="agent_classification",
            topic_processing=prompt_template_topic_processing,
        ),
    )

    result = _execute_agent(config_override=agent_config, messages=messages)

    mock_execute_topic.assert_called_once()

    _, called_kwargs = mock_execute_topic.call_args

    assert called_kwargs["topic"] == topic
    assert called_kwargs["messages"] == messages
    assert called_kwargs["prompt_template"] == prompt_template_topic_processing
    assert len(called_kwargs["steps_initial"]) == 1

    assert result.role == AgentConversationMessageRole.ASSISTANT
    assert result.content == assistant_message
    assert result.run
    assert result.run.steps == mocked_execute_topic_steps


def test_action_call_request_confirmation_fails_if_no_requests():
    topic_system_name = "test_topic"
    prompt_template_topic_processing = "topic_processing"

    agent_config = AgentVariantValue(
        topics=[
            AgentTopic(
                system_name=topic_system_name,
                name="",
                description="",
                instructions="Topic instructions",
                actions=[],
            ),
        ],
        prompt_templates=AgentPromptTemplates(
            classification="agent_classification",
            topic_processing=prompt_template_topic_processing,
        ),
    )

    messages: list[AgentConversationMessage] = [
        AgentConversationMessageUser(id="1", content="User's message"),
        AgentConversationMessageAssistant(
            id="2",
            topic=topic_system_name,
            run=AgentConversationRun(
                steps=[
                    AgentConversationRunStepTopicCompletion(
                        started_at=utc_now(),
                        details=AgentConversationTopicCompletion(
                            topic=AgentConversationSelectedTopic(
                                system_name=topic_system_name,
                                name="",
                                description="",
                            ),
                            assistant_message="Generated assistant message",
                        ),
                    ),
                ],
            ),
        ),
        AgentConversationMessageUser(
            id="3",
            action_call_confirmations=[
                AgentActionCallConfirmation(
                    request_id="call_id",
                    confirmed=True,
                ),
            ],
        ),
    ]

    with pytest.raises(AssertionError) as exc_info:
        _execute_agent(config_override=agent_config, messages=messages)

    assert "No action call requests found in the latest step" in str(exc_info.value)


def test_action_call_request_confirmation_executes_topic(mocker: MockerFixture):
    topic_system_name = "test_topic"
    action_call_request_id = "call_1"
    prompt_template_topic_processing = "topic_processing"
    topic = AgentTopic(
        system_name=topic_system_name,
        name="",
        description="",
        instructions="Topic instructions",
        actions=[],
    )

    agent_config = AgentVariantValue(
        topics=[topic],
        prompt_templates=AgentPromptTemplates(
            classification="agent_classification",
            topic_processing=prompt_template_topic_processing,
        ),
    )

    action_call_requests = [
        AgentActionCallRequest(
            id=action_call_request_id,
            function_name="",
            arguments={},
            action_type=AgentActionType.API,
            action_system_name="",
            action_display_name="Retrieve Contact Information",
            action_display_description="Retrieves detailed information for a specified contact.",
            action_tool_system_name="",
            requires_confirmation=True,
        ),
    ]

    action_call_confirmations = [
        AgentActionCallConfirmation(
            request_id=action_call_request_id,
            confirmed=True,
        ),
    ]

    messages: list[AgentConversationMessage] = [
        AgentConversationMessageUser(id="1", content="User's message"),
        AgentConversationMessageAssistant(
            id="2",
            topic=topic_system_name,
            run=AgentConversationRun(
                steps=[
                    AgentConversationRunStepTopicCompletion(
                        started_at=utc_now(),
                        details=AgentConversationTopicCompletion(
                            topic=AgentConversationSelectedTopic(
                                system_name=topic_system_name,
                                name="",
                                description="",
                            ),
                            action_call_requests=action_call_requests,
                        ),
                    ),
                ],
            ),
        ),
        AgentConversationMessageUser(
            id="3",
            action_call_confirmations=action_call_confirmations,
        ),
    ]

    action_step = AgentConversationRunStepTopicActionCall(
        started_at=utc_now(),
        details=AgentTopicActionCall(
            request=AgentActionCallRequest(
                id=action_call_request_id,
                function_name="",
                arguments={},
                action_type=AgentActionType.API,
                action_system_name="",
                action_display_name="Retrieve Contact Information",
                action_display_description="Retrieves detailed information for a specified contact.",
                action_tool_system_name="",
                requires_confirmation=True,
            ),
            response=AgentActionCallResponse(content="{}"),
        ),
    )

    mock_create_action_call_steps = mocker.patch(
        "services.agents.services.create_action_call_steps",
    )
    mock_create_action_call_steps.return_value = [action_step]

    mock_execute_topic = mocker.patch("services.agents.services.execute_topic")
    mock_execute_topic.return_value = AgentConversationExecuteTopicResult(
        content="Assistant message",
        steps=[],
    )

    _execute_agent(config_override=agent_config, messages=messages)

    mock_create_action_call_steps.assert_called_once_with(
        action_call_requests=action_call_requests,
        action_call_confirmations=action_call_confirmations,
    )

    mock_execute_topic.assert_called_once()
    _, called_kwargs = mock_execute_topic.call_args

    assert called_kwargs["topic"] == topic
    assert called_kwargs["messages"] == messages
    assert called_kwargs["prompt_template"] == prompt_template_topic_processing
    assert len(called_kwargs["steps_initial"]) == 1
    initial_step = called_kwargs["steps_initial"][0]

    assert isinstance(initial_step, AgentConversationRunStepTopicActionCall)
    assert initial_step == action_step
