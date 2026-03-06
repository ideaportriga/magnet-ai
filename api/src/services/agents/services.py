import asyncio
import json
import os
import re
import uuid
from logging import getLogger
from typing import Final

from advanced_alchemy.extensions.litestar import filters
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCall,
    ChatCompletionMessageToolCallParam,
    ChatCompletionToolParam,
)

from core.config.app import alchemy
from core.domain.agents.service import AgentsService
from core.domain.api_servers.service import ApiServersService
from core.domain.collections.schemas import Collection as CollectionSchema
from core.domain.collections.service import CollectionsService
from core.domain.mcp_servers.service import MCPServersService
from core.domain.rag_tools.schemas import RagTool as RagToolSchema
from core.domain.rag_tools.service import RagToolsService
from core.domain.retrieval_tools.schemas import RetrievalTool as RetrievalToolSchema
from core.domain.retrieval_tools.service import RetrievalToolsService
from open_ai.utils_new import create_chat_completion_from_prompt_template
from prompt_templates.prompt_templates import get_prompt_template_by_system_name_flat
from services.agents.actions.execute import execute_agent_action
from services.agents.models import (
    Agent,
    AgentAction,
    AgentActionCallConfirmation,
    AgentActionCallRequest,
    AgentActionCallRequestPublic,
    AgentActionCallResponse,
    AgentActionType,
    AgentConversationClassification,
    AgentConversationExecuteTopicResult,
    AgentConversationMessage,
    AgentConversationMessageAssistant,
    AgentConversationMessageRole,
    AgentConversationMessageUser,
    AgentConversationRun,
    AgentConversationRunStep,
    AgentConversationRunStepClassification,
    AgentConversationRunStepTopicActionCall,
    AgentConversationRunStepTopicCompletion,
    AgentConversationRunStepType,
    AgentConversationSelectedTopic,
    AgentConversationTopicCompletion,
    AgentTopic,
    AgentTopicActionCall,
    AgentVariantValue,
    ConversationIntent,
)
from services.api_servers.types import ApiServerConfig
from services.mcp_servers.types import McpServerConfig
from services.observability import observability_context, observe
from services.prompt_templates import execute_prompt_template
from utils.datetime_utils import utc_now

logger = getLogger(__name__)

CLASSIFICATION_PROMPT_TEMPLATE_PASS: Final = "PASS"


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
    else:
        if isinstance(system_name_or_config, str):
            agent_config = await get_agent_by_system_name(system_name_or_config)
        else:
            agent_config = system_name_or_config

        assert agent_config, "Agent not found"
        logger.info(f"Agent config: {agent_config}")
        prompt_templates = agent_config.active_variant_value.prompt_templates
        topics = agent_config.active_variant_value.topics

    run = AgentConversationRun(
        steps=[],
    )

    latest_message = messages[-1]

    if (
        isinstance(latest_message, AgentConversationMessageUser)
        and latest_message.action_call_confirmations
    ):
        latest_assistant_message = messages[-2]
        assert isinstance(latest_assistant_message, AgentConversationMessageAssistant)
        assert latest_assistant_message.run, "Latest message must have a run"
        assert latest_assistant_message.run.steps, "Latest message must have steps"

        latest_step = latest_assistant_message.run.steps[-1]

        assert isinstance(latest_step, AgentConversationRunStepTopicCompletion), (
            "Latest step must be a topic completion step"
        )

        assert latest_step.details.action_call_requests, (
            "No action call requests found in the latest step"
        )

        assert latest_assistant_message.topic, (
            "Topic is missing in the latest assistant message"
        )
        topic = next(
            (
                topic
                for topic in topics
                if topic.system_name == latest_assistant_message.topic
            ),
            None,
        )

        action_call_steps = await create_action_call_steps(
            action_call_requests=latest_step.details.action_call_requests,
            action_call_confirmations=latest_message.action_call_confirmations,
        )

        run.steps.extend(action_call_steps)

        assert topic, "Topic is not defined"

    # Experimental feature
    elif prompt_templates.classification == CLASSIFICATION_PROMPT_TEMPLATE_PASS:
        topic = next(iter(topics), None)
        assert topic, "No topics"

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
                content=classification.assistant_message,
                run=run,
            )

            return result

        topic_system_name = classification.topic

        if not topic_system_name:
            logger.warning("Classification returned intent='topic' but topic is empty")
            return AgentConversationMessageAssistant(
                id=uuid.uuid4(),
                content=classification.assistant_message,
                run=run,
            )

        topic = next(
            (topic for topic in topics if topic.system_name == topic_system_name),
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
                content=classification.assistant_message,
                run=run,
            )

    if not topic:
        raise ValueError("No topic found for the conversation")

    topic_execute_result = await execute_topic(
        topic=topic,
        messages=messages,
        prompt_template=prompt_templates.topic_processing,
        steps_initial=run.steps,
        variables=variables,
    )

    run.steps = topic_execute_result.steps

    result = AgentConversationMessageAssistant(
        id=uuid.uuid4(),
        topic=topic.system_name if topic else None,
        content=topic_execute_result.content,
        action_call_requests=topic_execute_result.action_call_requests,
        run=run,
    )

    return result


def _extract_json_string(text: str) -> str:
    """Best-effort extraction of a JSON object from LLM output.

    Handles common quirks: code fences, leading prose, trailing text.
    """
    stripped = text.strip()
    if not stripped:
        return stripped

    # Strip markdown code fences (```json ... ```)
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)```", stripped, re.DOTALL)
    if fence_match:
        stripped = fence_match.group(1).strip()

    # Try to isolate the outermost JSON object
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start >= 0 and end > start:
        return stripped[start : end + 1]

    return stripped


@observe(
    name="Determine intent & topic",
    description="Before processing user prompt, agent determines user's intent and conversation topic.",
)
async def classify_conversation(
    prompt_template: str,
    messages: list[AgentConversationMessage],
    topics: list[AgentTopic],
) -> AgentConversationClassification:
    valid_topic_system_names: set[str] = (
        {t.system_name for t in topics} if topics else set()
    )

    topic_definitions = "No topics."
    topic_system_names = ""

    if topics:
        topic_definitions = [
            {
                "system_name": topics.system_name,
                "name": topics.name,
                "description": topics.description,
            }
            for topics in topics
        ]

        topic_system_names = [topics.system_name for topics in topics]

    clean_conversation = [
        {"role": message.role, "content": message.content} for message in messages
    ]

    max_attempts = 2
    last_error: Exception | None = None
    last_result: AgentConversationClassification | None = None

    for attempt in range(max_attempts):
        prompt_template_result = await execute_prompt_template(
            system_name_or_config=prompt_template,
            template_values={
                "TOPIC_DEFINITIONS": topic_definitions,
                "TOPIC_SYSTEM_NAMES": topic_system_names,
            },
            template_additional_messages=[
                {
                    "role": "user",
                    "content": json.dumps(
                        clean_conversation, indent=2, ensure_ascii=False
                    ),
                },
            ],
        )

        raw_content = prompt_template_result.content or ""
        cleaned = _extract_json_string(raw_content)

        try:
            parsed = AgentConversationClassification.model_validate_json(cleaned)
            last_result = parsed

            # Validate: if intent is "topic", the topic must exist
            if parsed.intent == ConversationIntent.TOPIC:
                if not parsed.topic:
                    raise ValueError(
                        "Classification returned intent='topic' but topic is null"
                    )
                if parsed.topic not in valid_topic_system_names:
                    raise ValueError(
                        f"Classification returned unknown topic '{parsed.topic}'. "
                        f"Valid: {sorted(valid_topic_system_names)}"
                    )

            observability_context.update_current_span(
                input={
                    "User message": clean_conversation[-1]["content"],
                },
                output={
                    "Intent": parsed.intent,
                    "Topic": parsed.topic.upper() if parsed.topic else None,
                    "Reasoning": parsed.reason,
                },
            )
            return parsed
        except Exception as e:
            last_error = e
            logger.warning(
                "Classification attempt %d/%d failed: %s (raw=%s)",
                attempt + 1,
                max_attempts,
                e,
                raw_content[:200],
            )

    # All retries exhausted — return a safe fallback classification
    # instead of crashing. Use the last LLM-generated reason as assistant_message
    # so the response is in the conversation's language.
    logger.warning(
        "Classification failed after %d attempts, falling back to REQUEST_NOT_CLEAR",
        max_attempts,
    )
    if last_result and isinstance(last_result, AgentConversationClassification):
        last_result.intent = ConversationIntent.REQUEST_NOT_CLEAR
        last_result.topic = None
        if not last_result.assistant_message:
            last_result.assistant_message = last_result.reason
        return last_result

    return AgentConversationClassification(
        intent=ConversationIntent.REQUEST_NOT_CLEAR,
        reason=str(last_error) if last_error else "Classification failed",
        assistant_message=None,
    )


EXECUTE_TOPIC_MAX_ITERATIONS = 5
EXECUTE_TOPIC_TIMEOUT_SECONDS: Final[int] = int(
    os.environ.get("AGENT_TOPIC_TIMEOUT_SECONDS", "120")
)

ACTION_MESSAGE_ARGUMENT_NAME: Final = "_magnetActionMessage"

# TODO - avoid hardcoding
env = os.environ
ACTION_MESSAGE_DEFAULT_LLM_DESCRIPTION: Final[str] = env.get(
    "ACTION_MESSAGE_DEFAULT_LLM_DESCRIPTION",
    """
A short natural-language action summary to show the user.
It should clearly state what the action will do, including relevant argument values.
Focus on action, not the result.
""",
)


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
) -> AgentConversationExecuteTopicResult:
    selected_topic_data = AgentConversationSelectedTopic(
        name=topic.name,
        system_name=topic.system_name,
        description=topic.description,
    )
    iteration = 0
    actions = topic.actions
    actions_by_function_name = {action.function_name: action for action in actions}
    tools = await create_chat_completion_tools(topic.actions)

    prompt_template_config = await get_prompt_template_by_system_name_flat(
        prompt_template_system_name=prompt_template,
    )

    steps = steps_initial.copy() if steps_initial else []

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

                additional_completion_messages = generate_completion_messages(
                    all_messages
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
                    # Log and let the loop retry (next iteration will re-prompt).
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
                        action_call_response = await execute_agent_action(
                            action_call_request,
                        )
                    except Exception as e:
                        logger.exception(
                            "Action '%s' (type=%s) failed",
                            action_call_request.action_system_name,
                            action_call_request.action_type,
                        )
                        action_call_response = AgentActionCallResponse(
                            content=f"Error executing tool '{action_call_request.action_display_name}': {e}",
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
                    assert isinstance(
                        action_call_step, AgentConversationRunStepTopicActionCall
                    ), "Last step must be an action call step"
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
        raise ValueError(
            f"Agent topic execution timed out after {EXECUTE_TOPIC_TIMEOUT_SECONDS}s"
        )

    raise ValueError("Max iteration count reached")


def create_action_call_requests(
    tool_calls: list[ChatCompletionMessageToolCall] | None,
    actions_by_function_name: dict[str, AgentAction],
    variables: dict[str, str] | None = None,
) -> list[AgentActionCallRequest] | None:
    if not tool_calls:
        return None

    action_call_requests: list[AgentActionCallRequest] = []

    for tool_call in tool_calls:
        if tool_call.type != "function":
            logger.warning(f"Unsupported tool call of type {tool_call.type}")
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
            logger.warning(f'Action is missing for function "{function_name}"')
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


# TODO - Refactor
async def create_chat_completion_tools(
    actions: list[AgentAction],
) -> list[ChatCompletionToolParam]:
    chat_completion_tools: list[ChatCompletionToolParam] = []

    api_actions = [action for action in actions if action.type == AgentActionType.API]
    api_servers_by_system_name: dict[str, ApiServerConfig] = {}

    if api_actions:
        api_servers_by_system_name = await get_api_servers_by_system_name(api_actions)

    mcp_tool_actions = [
        action for action in actions if action.type == AgentActionType.MCP_TOOL
    ]

    mcp_servers_by_system_name: dict[str, McpServerConfig] = {}
    if mcp_tool_actions:
        mcp_servers_by_system_name = await get_mcp_servers_by_system_name(
            mcp_tool_actions
        )

    for action in actions:
        chat_completion_tool = await create_chat_completion_tool(
            action=action,
            api_servers_by_system_name=api_servers_by_system_name,
            mcp_servers_by_system_name=mcp_servers_by_system_name,
        )

        chat_completion_tools.append(chat_completion_tool)

    return chat_completion_tools


async def create_chat_completion_tool(
    action: AgentAction,
    api_servers_by_system_name: dict[str, ApiServerConfig],
    mcp_servers_by_system_name: dict[str, McpServerConfig],
) -> ChatCompletionToolParam:
    function_name = action.function_name
    function_description = action.function_description or ""

    parameters = await create_chat_completion_tool_parameters(
        action=action,
        api_servers_by_system_name=api_servers_by_system_name,
        mcp_servers_by_system_name=mcp_servers_by_system_name,
    )

    if action.requires_confirmation:
        parameters["properties"][ACTION_MESSAGE_ARGUMENT_NAME] = {
            "type": "string",
            "description": action.action_message_llm_description
            or ACTION_MESSAGE_DEFAULT_LLM_DESCRIPTION,
        }
        parameters["required"].append(ACTION_MESSAGE_ARGUMENT_NAME)

    chat_completion_tool: ChatCompletionToolParam = {
        "type": "function",
        "function": {
            "name": function_name,
            "description": function_description,
            "parameters": parameters,
        },
    }
    return chat_completion_tool


async def create_chat_completion_tool_parameters(
    action: AgentAction,
    api_servers_by_system_name: dict[str, ApiServerConfig],
    mcp_servers_by_system_name: dict[str, McpServerConfig],
) -> dict:
    match action.type:
        case AgentActionType.API:
            api_server_name = action.tool_provider
            assert api_server_name

            api_server = api_servers_by_system_name[api_server_name]

            assert api_server
            assert api_server.tools

            api_server_tool = next(
                (
                    tool
                    for tool in api_server.tools
                    if tool.system_name == action.tool_system_name
                ),
                None,
            )

            assert api_server_tool, (
                f"API server tool not found: {action.tool_system_name}"
            )

            return api_server_tool.parameters.input

        # Experimental feature
        case AgentActionType.MCP_TOOL:
            mcp_server_name = action.tool_provider
            assert mcp_server_name

            mcp_server = mcp_servers_by_system_name[mcp_server_name]
            assert mcp_server
            assert mcp_server.tools

            mcp_server_tool = next(
                (
                    tool
                    for tool in mcp_server.tools
                    if tool.name == action.tool_system_name
                ),
                None,
            )
            assert mcp_server_tool, (
                f"MCP server tool not found: {action.tool_system_name}"
            )

            return mcp_server_tool.inputSchema

        case AgentActionType.RAG | AgentActionType.RETRIEVAL:
            if action.type == AgentActionType.RAG:
                field_list = await get_metadata_fields_from_rag_tool(
                    action.tool_system_name
                )
            else:
                field_list = await get_metadata_fields_from_retrieval_tool(
                    action.tool_system_name
                )

            return {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Rephrased user query, without any filtering. This query will be used for vector search, so do not apply keyword approach.",
                    },
                    "metadata_filter": {
                        "type": "string",
                        "description": f"MongoDB-like filter object, that is used to narrow down knowledge source chunks. List of available operators: $and, $or, $eq, $ne, $in. Top level operator should be either $and or $or. List of fields, that can be used in filter:\n{'\n'.join(field_list)}",
                    },
                },
                "required": ["query"],
                "additionalProperties": False,
            }
        case AgentActionType.PROMPT_TEMPLATE:
            return {
                "type": "object",
                "properties": {
                    "userMessage": {
                        "type": "string",
                        "description": "User message",
                    },
                },
                "required": ["userMessage"],
                "additionalProperties": False,
            }
        case AgentActionType.KNOWLEDGE_GRAPH:
            from services.knowledge_graph.retrievers.agent_retriever.tools import (
                get_agent_tool_specs,
            )

            tool_specs = get_agent_tool_specs()
            spec = next(
                (s for s in tool_specs if s["name"] == action.tool_system_name),
                None,
            )
            if spec and spec.get("parameters"):
                return spec["parameters"]

            # Fallback for unknown tool names
            return {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Rephrased user query optimized for semantic similarity search against knowledge graph.",
                    },
                },
                "required": ["query"],
                "additionalProperties": False,
            }
        case _:
            raise ValueError(f"Unknown action type - {action.type}")


async def get_api_servers_by_system_name(
    api_actions: list[AgentAction],
) -> dict[str, ApiServerConfig]:
    api_server_names = list({action.tool_provider for action in api_actions})

    async with alchemy.get_session() as session:
        service = ApiServersService(session=session)
        api_servers = await service.list(
            filters.CollectionFilter(field_name="system_name", values=api_server_names),
        )

        api_servers_entities = [
            service.to_schema(api_server, schema_type=ApiServerConfig)
            for api_server in api_servers
        ]

        if len(api_servers_entities) != len(api_server_names):
            missing_servers = set(api_server_names) - {
                server.system_name for server in api_servers_entities
            }
            raise LookupError(
                f"API servers not found for system names: {missing_servers}"
            )

        api_servers_by_system_name = {
            mcp_server.system_name: mcp_server for mcp_server in api_servers_entities
        }

        return api_servers_by_system_name


async def get_mcp_servers_by_system_name(
    mcp_tool_actions: list[AgentAction],
) -> dict[str, McpServerConfig]:
    mcp_server_names = list({action.tool_provider for action in mcp_tool_actions})

    async with alchemy.get_session() as session:
        service = MCPServersService(session=session)
        mcp_servers = await service.list(
            filters.CollectionFilter(field_name="system_name", values=mcp_server_names),
        )
        mcp_servers_entities = [
            service.to_schema(server, schema_type=McpServerConfig)
            for server in mcp_servers
        ]

        if len(mcp_servers_entities) != len(mcp_server_names):
            missing_servers = set(mcp_server_names) - {
                server.system_name for server in mcp_servers_entities
            }
            raise LookupError(
                f"MCP servers not found for system names: {missing_servers}"
            )
        # Get each MCP server by system_name

        mcp_servers_by_system_name = {
            mcp_server.system_name: mcp_server for mcp_server in mcp_servers_entities
        }

        return mcp_servers_by_system_name


async def get_metadata_fields_from_rag_tool(system_name: str):
    async with alchemy.get_session() as session:
        rag_service = RagToolsService(session=session)
        rag_tool_entity = await rag_service.get_one_or_none(system_name=system_name)

        if not rag_tool_entity:
            return []

        rag_tool = rag_service.to_schema(rag_tool_entity, schema_type=RagToolSchema)
        rag_tool_dict = rag_tool.model_dump()

        active_variant_name = rag_tool_dict.get("active_variant")
        active_variant = next(
            (
                variant
                for variant in rag_tool_dict.get("variants", [])
                if variant.get("variant") == active_variant_name
            ),
            {},
        )
        if not active_variant:
            return []

        knowledge_sources = active_variant.get("retrieve", {}).get(
            "collection_system_names", []
        )

        collections_service = CollectionsService(session=session)
        collections_entities = await collections_service.list(
            filters.CollectionFilter(
                field_name="system_name", values=knowledge_sources
            ),
        )

        metadata_fields = {}
        for knowledge_source_entity in collections_entities:
            knowledge_source = collections_service.to_schema(
                knowledge_source_entity, schema_type=CollectionSchema
            )
            knowledge_source_dict = knowledge_source.model_dump()

            knowledge_source_metadata_fields = [
                config
                for config in knowledge_source_dict.get("metadata_config") or []
                if config.get("enabled")
            ]
            for field in knowledge_source_metadata_fields:
                metadata_fields[field.get("name")] = (
                    f"- {field.get('name')}:{field.get('description')}"
                )

        return metadata_fields


async def get_metadata_fields_from_retrieval_tool(system_name: str):
    async with alchemy.get_session() as session:
        retrieval_service = RetrievalToolsService(session=session)
        retrieval_tool_entity = await retrieval_service.get_one_or_none(
            system_name=system_name
        )

        if not retrieval_tool_entity:
            return []

        retrieval_tool = retrieval_service.to_schema(
            retrieval_tool_entity, schema_type=RetrievalToolSchema
        )
        retrieval_tool_dict = retrieval_tool.model_dump()

        knowledge_sources = retrieval_tool_dict.get("retrieve", {}).get(
            "collection_system_names", []
        )

        collections_service = CollectionsService(session=session)
        collections_entities = await collections_service.list(
            filters.CollectionFilter(
                field_name="system_name", values=knowledge_sources
            ),
        )

        metadata_fields = {}
        for knowledge_source_entity in collections_entities:
            knowledge_source = collections_service.to_schema(
                knowledge_source_entity, schema_type=CollectionSchema
            )
            knowledge_source_dict = knowledge_source.model_dump()

            knowledge_source_metadata_fields = [
                config
                for config in knowledge_source_dict.get("metadata_config") or []
                if config.get("enabled")
            ]
            for field in knowledge_source_metadata_fields:
                metadata_fields[field.get("name")] = (
                    f"- {field.get('name')}:{field.get('description')}"
                )

        return metadata_fields


def generate_completion_messages(
    messages: list[AgentConversationMessage],
) -> list[ChatCompletionMessageParam]:
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


async def get_agent_by_system_name(system_name: str) -> Agent:
    async with alchemy.get_session() as session:
        service = AgentsService(session=session)
        agent_entity = await service.get_one_or_none(system_name=system_name)

        if not agent_entity:
            raise LookupError(f"Agent with system_name '{system_name}' not found")

        agent_schema = service.to_schema(agent_entity, schema_type=Agent)

        # Convert schema to models Agent
        # agent = Agent.model_validate(agent_schema.model_dump())

        return agent_schema


async def create_action_call_steps(
    action_call_requests: list[AgentActionCallRequest],
    action_call_confirmations: list[AgentActionCallConfirmation],
) -> list[AgentConversationRunStep]:
    confirmations_by_request_id = {
        confirmation.request_id: confirmation
        for confirmation in action_call_confirmations
    }

    steps = []

    for action_call_request in action_call_requests:
        confirmation = confirmations_by_request_id.get(action_call_request.id)

        if action_call_request.requires_confirmation:
            if not confirmation:
                raise ValueError(
                    f"Confirmation missing for action call request ID: {action_call_request.id}"
                )

            if not confirmation.confirmed:
                error_message = f"Error: User denied execution of this tool. Comment: {confirmation.comment}"
                action_call_step = AgentConversationRunStepTopicActionCall(
                    started_at=utc_now(),
                    details=AgentTopicActionCall(
                        request=action_call_request,
                        response=AgentActionCallResponse(content=error_message),
                    ),
                )
                steps.append(action_call_step)
                continue

        action_call_step_started_at = utc_now()

        try:
            action_call_response = await execute_agent_action(action_call_request)
        except Exception as e:
            logger.exception(
                "Confirmed action '%s' (type=%s) failed",
                action_call_request.action_system_name,
                action_call_request.action_type,
            )
            action_call_response = AgentActionCallResponse(
                content=f"Error executing tool '{action_call_request.action_display_name}': {e}",
            )

        action_call_step = AgentConversationRunStepTopicActionCall(
            started_at=action_call_step_started_at,
            details=AgentTopicActionCall(
                request=action_call_request,
                response=action_call_response,
            ),
        )
        steps.append(action_call_step)

    return steps
