"""Agent orchestration — top-level entry point for agent conversations.

This module is the thin orchestrator that delegates to specialised sub-modules:
- classification.py — intent detection & topic routing
- topic_execution.py — main agent loop
- confirmation.py — action call confirmation handling
- tool_schema.py — ChatCompletionTool construction
- message_builder.py — conversation → ChatCompletion message conversion
- memory.py — conversation context strategies
- exceptions.py — custom exception hierarchy
"""

import uuid
from logging import getLogger
from typing import Final

from core.config.app import alchemy
from core.domain.agents.service import AgentsService
from services.agents.classification import classify_conversation
from services.agents.confirmation import create_action_call_steps
from services.agents.exceptions import (
    AgentConfigurationError,
    AgentLoopExhaustedError,
    AgentNotFoundError,
    AgentTimeoutError,
)
from services.agents.models import (
    Agent,
    AgentConversationExecuteTopicResult,
    AgentConversationMessage,
    AgentConversationMessageAssistant,
    AgentConversationMessageUser,
    AgentConversationRun,
    AgentConversationRunStepClassification,
    AgentConversationRunStepTopicCompletion,
    AgentVariantValue,
    ConversationIntent,
)
from services.agents.topic_execution import execute_topic
from services.observability import observe
from utils.datetime_utils import utc_now

logger = getLogger(__name__)

CLASSIFICATION_PROMPT_TEMPLATE_PASS: Final = "PASS"

DEFAULT_FALLBACK_MESSAGE: Final = (
    "I'm sorry, I wasn't able to process your request. "
    "Could you please try again or rephrase your question?"
)

# Re-export for backward compatibility
from services.agents.message_builder import (  # noqa: E402,F401
    create_tool_calls_from_topic_completion_step,
    generate_completion_messages,
)
from services.agents.tool_schema import (  # noqa: E402,F401
    ACTION_MESSAGE_ARGUMENT_NAME,
    create_chat_completion_tool,
    create_chat_completion_tool_parameters,
    create_chat_completion_tools,
    get_api_servers_by_system_name,
    get_mcp_servers_by_system_name,
    get_metadata_fields_from_rag_tool,
    get_metadata_fields_from_retrieval_tool,
)
from services.agents.topic_execution import (  # noqa: E402,F401
    EXECUTE_TOPIC_MAX_ITERATIONS,
    EXECUTE_TOPIC_TIMEOUT_SECONDS,
    create_action_call_requests,
)


@observe(name="Process conversation")
async def execute_agent(
    *,
    system_name_or_config: str | Agent | None = None,
    messages: list[AgentConversationMessage],
    config_override: AgentVariantValue | None = None,
    variables: dict[str, str] | None = None,
) -> AgentConversationMessageAssistant:
    if config_override:
        prompt_templates = config_override.prompt_templates
        topics = config_override.topics
        settings = config_override.settings
    else:
        if isinstance(system_name_or_config, str):
            agent_config = await get_agent_by_system_name(system_name_or_config)
        else:
            agent_config = system_name_or_config

        if not agent_config:
            raise AgentNotFoundError("Agent not found")
        logger.info("Agent config: %s", agent_config)
        prompt_templates = agent_config.active_variant_value.prompt_templates
        topics = agent_config.active_variant_value.topics
        settings = agent_config.active_variant_value.settings

    run = AgentConversationRun(
        steps=[],
    )

    latest_message = messages[-1]

    if (
        isinstance(latest_message, AgentConversationMessageUser)
        and latest_message.action_call_confirmations
    ):
        latest_assistant_message = messages[-2]
        if not isinstance(latest_assistant_message, AgentConversationMessageAssistant):
            raise AgentConfigurationError(
                "Expected assistant message before user confirmation"
            )
        if not latest_assistant_message.run:
            raise AgentConfigurationError("Latest message must have a run")
        if not latest_assistant_message.run.steps:
            raise AgentConfigurationError("Latest message must have steps")

        latest_step = latest_assistant_message.run.steps[-1]

        if not isinstance(latest_step, AgentConversationRunStepTopicCompletion):
            raise AgentConfigurationError("Latest step must be a topic completion step")

        if not latest_step.details.action_call_requests:
            raise AgentConfigurationError(
                "No action call requests found in the latest step"
            )

        if not latest_assistant_message.topic:
            raise AgentConfigurationError(
                "Topic is missing in the latest assistant message"
            )
        topic = next(
            (t for t in topics if t.system_name == latest_assistant_message.topic),
            None,
        )

        action_call_steps = await create_action_call_steps(
            action_call_requests=latest_step.details.action_call_requests,
            action_call_confirmations=latest_message.action_call_confirmations,
        )

        run.steps.extend(action_call_steps)

        if not topic:
            raise AgentConfigurationError("Topic is not defined")

    # Experimental feature
    elif prompt_templates.classification == CLASSIFICATION_PROMPT_TEMPLATE_PASS:
        topic = next(iter(topics), None)
        if not topic:
            raise AgentConfigurationError("No topics configured for this agent")

    else:
        classification_step_started_at = utc_now()
        classification = await classify_conversation(
            prompt_template=prompt_templates.classification,
            messages=messages,
            topics=topics,
        )
        classification_step = AgentConversationRunStepClassification(
            started_at=classification_step_started_at,
            completed_at=utc_now(),
            details=classification,
        )

        run.steps.append(classification_step)

        if classification.intent != ConversationIntent.TOPIC:
            result = AgentConversationMessageAssistant(
                id=uuid.uuid4(),
                content=classification.assistant_message
                or classification.reason
                or DEFAULT_FALLBACK_MESSAGE,
                run=run,
            )

            return result

        topic_system_name = classification.topic

        if not topic_system_name:
            logger.warning("Classification returned intent='topic' but topic is empty")
            return AgentConversationMessageAssistant(
                id=uuid.uuid4(),
                content=classification.assistant_message
                or classification.reason
                or DEFAULT_FALLBACK_MESSAGE,
                run=run,
            )

        topic = next(
            (t for t in topics if t.system_name == topic_system_name),
            None,
        )

        if not topic:
            logger.warning(
                "Classification returned unknown topic '%s', available: %s",
                topic_system_name,
                [t.system_name for t in topics],
            )
            return AgentConversationMessageAssistant(
                id=uuid.uuid4(),
                content=classification.assistant_message
                or classification.reason
                or DEFAULT_FALLBACK_MESSAGE,
                run=run,
            )

    if not topic:
        raise AgentConfigurationError("No topic found for the conversation")

    # Resolve memory_last_n_messages from agent settings if available
    memory_n = (
        settings.memory_last_n_messages
        if settings and settings.memory_last_n_messages
        else None
    )

    try:
        topic_execute_result = await execute_topic(
            topic=topic,
            messages=messages,
            prompt_template=prompt_templates.topic_processing,
            steps_initial=run.steps,
            variables=variables,
            **({"memory_last_n_messages": memory_n} if memory_n is not None else {}),
        )
    except (AgentTimeoutError, AgentLoopExhaustedError) as e:
        logger.error("Topic execution failed for '%s': %s", topic.system_name, e)
        topic_execute_result = AgentConversationExecuteTopicResult(
            content=DEFAULT_FALLBACK_MESSAGE,
            steps=run.steps,
        )

    run.steps = topic_execute_result.steps

    result = AgentConversationMessageAssistant(
        id=uuid.uuid4(),
        topic=topic.system_name if topic else None,
        content=topic_execute_result.content,
        action_call_requests=topic_execute_result.action_call_requests,
        run=run,
    )

    # Guarantee: if there are no action_call_requests (confirmation buttons),
    # the response must always contain a non-empty content for the user.
    if not result.action_call_requests and not result.content:
        result.content = DEFAULT_FALLBACK_MESSAGE

    return result


async def get_agent_by_system_name(system_name: str) -> Agent:
    async with alchemy.get_session() as session:
        service = AgentsService(session=session)
        agent_entity = await service.get_one_or_none(system_name=system_name)

        if not agent_entity:
            raise AgentNotFoundError(
                f"Agent with system_name '{system_name}' not found"
            )

        agent_schema = service.to_schema(agent_entity, schema_type=Agent)

        return agent_schema


# Backward-compat alias used by tests
_execute_agent = execute_agent
