"""Tool schema generation — builds ChatCompletionToolParam from agent actions."""

import os
import re
from logging import getLogger
from typing import Final

from advanced_alchemy.extensions.litestar import filters
from openai.types.chat import ChatCompletionToolParam

from core.config.app import alchemy
from core.domain.api_servers.service import ApiServersService
from core.domain.collections.schemas import Collection as CollectionSchema
from core.domain.collections.service import CollectionsService
from core.domain.mcp_servers.service import MCPServersService
from core.domain.rag_tools.schemas import RagTool as RagToolSchema
from core.domain.rag_tools.service import RagToolsService
from core.domain.retrieval_tools.schemas import RetrievalTool as RetrievalToolSchema
from core.domain.retrieval_tools.service import RetrievalToolsService
from services.agents.exceptions import AgentConfigurationError
from services.agents.models import AgentAction, AgentActionType
from services.api_servers.types import ApiServerConfig
from services.mcp_servers.types import McpServerConfig

logger = getLogger(__name__)

ACTION_MESSAGE_ARGUMENT_NAME: Final = "_magnetActionMessage"

_INVALID_FUNCTION_NAME_CHARS_RE = re.compile(r"[^a-zA-Z0-9_-]")


def sanitize_function_name(name: str) -> str:
    """Replace characters not allowed in OpenAI function names with underscores."""
    return _INVALID_FUNCTION_NAME_CHARS_RE.sub("_", name)


# TODO - avoid hardcoding
_env = os.environ
ACTION_MESSAGE_DEFAULT_LLM_DESCRIPTION: Final[str] = _env.get(
    "ACTION_MESSAGE_DEFAULT_LLM_DESCRIPTION",
    """
A short natural-language action summary to show the user.
It should clearly state what the action will do, including relevant argument values.
Focus on action, not the result.
""",
)


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
    function_name = sanitize_function_name(action.function_name)
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
            if not api_server_name:
                raise AgentConfigurationError(
                    f"API action '{action.system_name}' has no tool_provider"
                )

            api_server = api_servers_by_system_name.get(api_server_name)
            if not api_server or not api_server.tools:
                raise AgentConfigurationError(
                    f"API server '{api_server_name}' not found or has no tools"
                )

            api_server_tool = next(
                (
                    tool
                    for tool in api_server.tools
                    if tool.system_name == action.tool_system_name
                ),
                None,
            )

            if not api_server_tool:
                raise AgentConfigurationError(
                    f"API server tool not found: {action.tool_system_name}"
                )

            return api_server_tool.parameters.input

        # Experimental feature
        case AgentActionType.MCP_TOOL:
            mcp_server_name = action.tool_provider
            if not mcp_server_name:
                raise AgentConfigurationError(
                    f"MCP action '{action.system_name}' has no tool_provider"
                )

            mcp_server = mcp_servers_by_system_name.get(mcp_server_name)
            if not mcp_server or not mcp_server.tools:
                raise AgentConfigurationError(
                    f"MCP server '{mcp_server_name}' not found or has no tools"
                )

            mcp_server_tool = next(
                (
                    tool
                    for tool in mcp_server.tools
                    if tool.name == action.tool_system_name
                ),
                None,
            )
            if not mcp_server_tool:
                raise AgentConfigurationError(
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
                        "description": f"Optional MongoDB-like filter to narrow down knowledge source chunks. Omit this field entirely if no filtering is needed. When filtering is needed, use operators: $and, $or, $eq, $ne, $in. List of fields available for filtering:\n{'\n'.join(field_list)}",
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
            server.system_name: server for server in api_servers_entities
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
