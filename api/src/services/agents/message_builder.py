"""Message builder — converts conversation history into ChatCompletion messages."""

import json
from logging import getLogger

from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCallParam,
)

from services.agents.models import (
    AgentConversationMessage,
    AgentConversationMessageRole,
    AgentConversationRunStepTopicCompletion,
    AgentConversationRunStepType,
)

logger = getLogger(__name__)


def generate_completion_messages(
    messages: list[AgentConversationMessage],
    max_messages: int | None = None,
) -> list[ChatCompletionMessageParam]:
    """Convert conversation messages into ChatCompletion message format.

    Args:
        messages: Full list of conversation messages.
        max_messages: If set, only the last N messages are used for context.
                      The current (latest) message is always included.
    """
    if max_messages is not None and len(messages) > max_messages:
        messages = messages[-max_messages:]

    completion_messages: list[ChatCompletionMessageParam] = []

    for message in messages:
        if message.role == AgentConversationMessageRole.USER:
            if message.content:
                completion_messages.append(
                    {
                        "role": "user",
                        "content": message.content,
                    },
                )
            continue

        if message.role == AgentConversationMessageRole.ASSISTANT:
            if not message.run:
                completion_messages.append(
                    {
                        "role": "assistant",
                        "content": message.content,
                    },
                )
                continue

            for step in message.run.steps:
                if (
                    step.type == AgentConversationRunStepType.CLASSIFICATION
                    and step.details.assistant_message
                ):
                    completion_messages.append(
                        {
                            "role": "assistant",
                            "content": step.details.assistant_message,
                        },
                    )
                    continue

                if step.type == AgentConversationRunStepType.TOPIC_COMPLETION:
                    assistant_message: ChatCompletionAssistantMessageParam = {
                        "role": "assistant",
                        "content": step.details.assistant_message,
                    }

                    tool_calls = create_tool_calls_from_topic_completion_step(step)

                    if tool_calls:
                        assistant_message["tool_calls"] = tool_calls

                    completion_messages.append(assistant_message)
                    continue

                if step.type == AgentConversationRunStepType.TOPIC_ACTION_CALL:
                    completion_messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": step.details.request.id,
                            "content": json.dumps(
                                step.details.response.content,
                                ensure_ascii=False,
                            ),
                        },
                    )
                    continue

    return completion_messages


def create_tool_calls_from_topic_completion_step(
    step: AgentConversationRunStepTopicCompletion,
) -> list[ChatCompletionMessageToolCallParam] | None:
    action_call_requests = step.details.action_call_requests

    if not action_call_requests:
        return None

    tool_calls = []

    for action_call_request in action_call_requests:
        tool_call = ChatCompletionMessageToolCallParam(
            id=action_call_request.id,
            type="function",
            function={
                "name": action_call_request.function_name,
                "arguments": json.dumps(
                    action_call_request.arguments, ensure_ascii=False
                ),
            },
        )
        tool_calls.append(tool_call)

    return tool_calls
