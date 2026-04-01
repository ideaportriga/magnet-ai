"""Topic execution — the main agent loop that processes a selected topic."""

import asyncio
import json
import os
import uuid
from logging import getLogger
from typing import Final

from openai.types.chat import ChatCompletion

from open_ai.utils_new import create_chat_completion_from_prompt_template
from prompt_templates.prompt_templates import get_prompt_template_by_system_name_flat
from services.agents.actions.execute import execute_agent_action
from services.agents.exceptions import (
    AgentLoopExhaustedError,
    AgentTimeoutError,
)
from services.agents.memory import DEFAULT_LAST_N_MESSAGES, create_memory_strategy
from services.agents.models import MemoryStrategyType
from services.agents.message_builder import generate_completion_messages
from services.agents.models import (
    AgentAction,
    AgentActionCallRequest,
    AgentActionCallRequestPublic,
    AgentActionCallResponse,
    AgentConversationExecuteTopicResult,
    AgentConversationMessage,
    AgentConversationMessageAssistant,
    AgentConversationRun,
    AgentConversationRunStep,
    AgentConversationRunStepTopicActionCall,
    AgentConversationRunStepTopicCompletion,
    AgentConversationSelectedTopic,
    AgentConversationTopicCompletion,
    AgentTopic,
    AgentTopicActionCall,
)
from services.agents.tool_schema import (
    ACTION_MESSAGE_ARGUMENT_NAME,
    create_chat_completion_tools,
    sanitize_function_name,
)
from services.observability import observe
from utils.datetime_utils import utc_now

logger = getLogger(__name__)

EXECUTE_TOPIC_MAX_ITERATIONS: Final[int] = 5
EXECUTE_TOPIC_TIMEOUT_SECONDS: Final[int] = int(
    os.environ.get("AGENT_TOPIC_TIMEOUT_SECONDS", "120")
)
EXECUTE_ACTION_TIMEOUT_SECONDS: Final[int] = int(
    os.environ.get("AGENT_ACTION_TIMEOUT_SECONDS", "120")
)


def _sanitize_action_error(e: Exception) -> str:
    """Return a user-safe error description without leaking internal details."""
    return "The tool encountered an error. Please try again or rephrase your request."


@observe(
    name="Main agent loop",
    description="Agent processes user prompt and returns a result. It may call available tools (APIs, RAGs, Prompt Templates) to fulfill user request.",
)
async def execute_topic(
    topic: AgentTopic,
    messages: list[AgentConversationMessage],
    prompt_template: str,
    steps_initial: list[AgentConversationRunStep] | None = None,
    variables: dict[str, str] | None = None,
    memory_strategy_type: MemoryStrategyType = MemoryStrategyType.LAST_N,
    memory_last_n_messages: int = DEFAULT_LAST_N_MESSAGES,
) -> AgentConversationExecuteTopicResult:
    selected_topic_data = AgentConversationSelectedTopic(
        name=topic.name,
        system_name=topic.system_name,
        description=topic.description,
    )
    iteration = 0
    actions = topic.actions
    actions_by_function_name = {
        sanitize_function_name(action.function_name): action for action in actions
    }
    tools = await create_chat_completion_tools(topic.actions)

    prompt_template_config = await get_prompt_template_by_system_name_flat(
        prompt_template_system_name=prompt_template,
    )

    steps = steps_initial.copy() if steps_initial else []

    memory_strategy = create_memory_strategy(
        memory_strategy_type, memory_last_n_messages
    )

    try:
        async with asyncio.timeout(EXECUTE_TOPIC_TIMEOUT_SECONDS):
            while iteration < EXECUTE_TOPIC_MAX_ITERATIONS:
                iteration += 1

                assistant_message = AgentConversationMessageAssistant(
                    id=uuid.uuid4(),
                    content=None,
                    run=AgentConversationRun(steps=steps),
                    topic=topic.system_name,
                )

                all_messages = messages + [assistant_message]
                context_messages = memory_strategy.select_messages(all_messages)

                additional_completion_messages = generate_completion_messages(
                    context_messages
                )

                topic_completion_step_started_at = utc_now()

                chat_completion_result = (
                    await create_chat_completion_from_prompt_template(
                        prompt_template_config=prompt_template_config,
                        additional_messages=additional_completion_messages,
                        prompt_template_values={
                            "TOPIC_NAME": topic.name,
                            "TOPIC_INSTRUCTIONS": topic.instructions
                            or "No instructions.",
                            **(variables or {}),
                        },
                        tools=tools,  # type: ignore
                    )
                )

                chat_completion: ChatCompletion = chat_completion_result[0]
                completion_message = chat_completion.choices[0].message

                action_call_requests = create_action_call_requests(
                    tool_calls=completion_message.tool_calls,
                    actions_by_function_name=actions_by_function_name,
                    variables=variables,
                )

                action_call_requests_to_confirm = (
                    [
                        request
                        for request in action_call_requests
                        if request.requires_confirmation
                    ]
                    if action_call_requests
                    else None
                )

                topic_completion_step = AgentConversationRunStepTopicCompletion(
                    started_at=topic_completion_step_started_at,
                    details=AgentConversationTopicCompletion(
                        topic=selected_topic_data,
                        assistant_message=completion_message.content,
                        action_call_requests=action_call_requests,
                    ),
                )

                steps.append(topic_completion_step)

                if action_call_requests_to_confirm:
                    result = AgentConversationExecuteTopicResult(
                        content=None,
                        steps=steps,
                        action_call_requests=[
                            AgentActionCallRequestPublic(
                                id=request.id,
                                action_message=request.action_message
                                or request.action_display_name,
                            )
                            for request in action_call_requests_to_confirm
                        ],
                    )

                    return result

                if topic_completion_step.details.assistant_message:
                    result = AgentConversationExecuteTopicResult(
                        content=topic_completion_step.details.assistant_message,
                        steps=steps,
                    )
                    return result

                if not action_call_requests:
                    # LLM returned neither text nor tool calls — empty response.
                    logger.warning(
                        "LLM returned empty response (no content, no tool calls) "
                        "on iteration %d/%d",
                        iteration,
                        EXECUTE_TOPIC_MAX_ITERATIONS,
                    )
                    continue

                for action_call_request in action_call_requests:
                    action_call_step_started_at = utc_now()

                    try:
                        async with asyncio.timeout(EXECUTE_ACTION_TIMEOUT_SECONDS):
                            action_call_response = await execute_agent_action(
                                action_call_request,
                            )
                    except TimeoutError:
                        logger.error(
                            "Action '%s' (type=%s) timed out after %ds",
                            action_call_request.action_system_name,
                            action_call_request.action_type,
                            EXECUTE_ACTION_TIMEOUT_SECONDS,
                        )
                        action_call_response = AgentActionCallResponse(
                            content=_sanitize_action_error(
                                TimeoutError("Action timed out")
                            ),
                        )
                    except Exception as e:
                        logger.exception(
                            "Action '%s' (type=%s) failed",
                            action_call_request.action_system_name,
                            action_call_request.action_type,
                        )
                        action_call_response = AgentActionCallResponse(
                            content=_sanitize_action_error(e),
                        )

                    action_call_step = AgentConversationRunStepTopicActionCall(
                        started_at=action_call_step_started_at,
                        details=AgentTopicActionCall(
                            request=action_call_request,
                            response=action_call_response,
                        ),
                    )

                    steps.append(action_call_step)

                # Experimental feature. Allows to skip topic processing and use action response as assistant message.
                if (
                    len(action_call_requests) == 1
                    and action_call_requests[0].use_response_as_assistant_message
                ):
                    action_call_step = steps[-1]
                    if not isinstance(
                        action_call_step, AgentConversationRunStepTopicActionCall
                    ):
                        raise AgentLoopExhaustedError(
                            "Expected last step to be an action call step"
                        )
                    action_call_response_content = (
                        action_call_step.details.response.content
                    )

                    assistant_message.content = action_call_response_content
                    result = AgentConversationExecuteTopicResult(
                        content=action_call_response_content,
                        steps=steps,
                    )
                    return result

    except TimeoutError:
        raise AgentTimeoutError(
            f"Agent topic execution timed out after {EXECUTE_TOPIC_TIMEOUT_SECONDS}s"
        )

    # Graceful degradation: instead of crashing, return partial results
    logger.error(
        "Agent loop exhausted after %d iterations for topic '%s'. "
        "Returning last available content.",
        EXECUTE_TOPIC_MAX_ITERATIONS,
        topic.system_name,
    )

    # Try to extract the last assistant message from the collected steps
    last_content: str | None = None
    for step in reversed(steps):
        if (
            isinstance(step, AgentConversationRunStepTopicCompletion)
            and step.details.assistant_message
        ):
            last_content = step.details.assistant_message
            break

    if last_content:
        return AgentConversationExecuteTopicResult(
            content=last_content,
            steps=steps,
        )

    raise AgentLoopExhaustedError(
        f"Agent loop exhausted after {EXECUTE_TOPIC_MAX_ITERATIONS} iterations "
        f"without producing a response for topic '{topic.system_name}'"
    )


def create_action_call_requests(
    tool_calls: list | None,
    actions_by_function_name: dict[str, AgentAction],
    variables: dict[str, str] | None = None,
) -> list[AgentActionCallRequest] | None:
    if not tool_calls:
        return None

    action_call_requests: list[AgentActionCallRequest] = []

    for tool_call in tool_calls:
        if tool_call.type != "function":
            logger.warning("Unsupported tool call of type %s", tool_call.type)
            continue

        function = tool_call.function
        function_name = function.name
        try:
            arguments: dict = json.loads(function.arguments)
        except json.JSONDecodeError:
            logger.warning(
                "Malformed JSON in tool call arguments for '%s': %s",
                function_name,
                function.arguments[:200],
            )
            continue
        action = actions_by_function_name.get(function_name)

        if not action:
            logger.warning("Action is missing for function '%s'", function_name)
            continue

        action_message = arguments.pop(
            ACTION_MESSAGE_ARGUMENT_NAME,
            action.display_name,
        )

        action_call_requests.append(
            AgentActionCallRequest(
                id=tool_call.id,
                function_name=function_name,
                arguments=arguments,
                action_type=action.type,
                action_system_name=action.system_name,
                action_tool_system_name=action.tool_system_name,
                action_tool_provider=action.tool_provider,
                action_display_name=action.display_name,
                action_display_description=action.display_description,
                requires_confirmation=action.requires_confirmation,
                use_response_as_assistant_message=action.use_response_as_assistant_message,
                action_message=action_message,
                variables=variables,
            ),
        )

    return action_call_requests
