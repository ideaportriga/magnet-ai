from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Annotated, Any, Mapping
from uuid import UUID

from advanced_alchemy.extensions.litestar import filters, providers, service
from litestar import Controller, Request, delete, get, patch, post
from litestar.params import Dependency, Parameter

from core.config.constants import DEFAULT_PAGINATION_SIZE
from core.domain.agents.service import (
    AgentsService,
)

from .schemas import Agent, AgentCreate, AgentUpdate

if TYPE_CHECKING:
    pass


class AgentsController(Controller):
    """Agents CRUD"""

    path = "/sql_agents"
    tags = ["Admin / Agents"]

    dependencies = providers.create_service_dependencies(
        AgentsService,
        "agents_service",
        filters={
            "pagination_type": "limit_offset",
            "id_filter": UUID,
            "search": "name",
            "search_ignore_case": True,
            "pagination_size": DEFAULT_PAGINATION_SIZE,
        },
    )

    @get()
    async def list_agents(
        self,
        agents_service: AgentsService,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
    ) -> service.OffsetPagination[Agent]:
        """List agents with pagination and filtering."""
        results, total = await agents_service.list_and_count(*filters)
        return agents_service.to_schema(
            results, total, filters=filters, schema_type=Agent
        )

    @post()
    async def create_agent(
        self, agents_service: AgentsService, data: AgentCreate, request: Request
    ) -> Agent:
        """Create a new agent."""
        obj = await agents_service.create(data)
        await _sync_runtime_caches(
            request=request,
            previous_channels=None,
            current_channels=getattr(obj, "channels", None),
        )
        return agents_service.to_schema(obj, schema_type=Agent)

    @get("/code/{code:str}")
    async def get_agent_by_code(
        self, agents_service: AgentsService, code: str
    ) -> Agent:
        """Get an agent by its system_name."""
        obj = await agents_service.get_one(system_name=code)
        return agents_service.to_schema(obj, schema_type=Agent)

    @get("/{agent_id:uuid}")
    async def get_agent(
        self,
        agents_service: AgentsService,
        agent_id: UUID = Parameter(
            title="Agent ID",
            description="The agent to retrieve.",
        ),
    ) -> Agent:
        """Get an agent by its ID."""
        obj = await agents_service.get(agent_id)
        return agents_service.to_schema(obj, schema_type=Agent)

    @patch("/{agent_id:uuid}")
    async def update_agent(
        self,
        agents_service: AgentsService,
        data: AgentUpdate,
        request: Request,
        agent_id: UUID = Parameter(
            title="Agent ID",
            description="The agent to update.",
        ),
    ) -> Agent:
        """Update an agent."""
        existing_obj = await agents_service.get(agent_id)
        previous_channels = deepcopy(getattr(existing_obj, "channels", None))
        obj = await agents_service.update(data, item_id=agent_id, auto_commit=True)
        await _sync_runtime_caches(
            request=request,
            previous_channels=previous_channels,
            current_channels=getattr(obj, "channels", None),
        )
        return agents_service.to_schema(obj, schema_type=Agent)

    @delete("/{agent_id:uuid}")
    async def delete_agent(
        self,
        agents_service: AgentsService,
        agent_id: UUID = Parameter(
            title="Agent ID",
            description="The agent to delete.",
        ),
    ) -> None:
        """Delete an agent from the system."""
        _ = await agents_service.delete(agent_id)


async def _sync_runtime_caches(
    *,
    request: Request,
    previous_channels: Mapping[str, Any] | None,
    current_channels: Mapping[str, Any] | None,
) -> None:
    teams_changed = _channel_enabled_changed(
        previous_channels=previous_channels,
        current_channels=current_channels,
        section="ms_teams",
    )

    if teams_changed:
        teams_cache = getattr(request.app.state, "teams_runtime_cache", None)
        if teams_cache is not None and hasattr(teams_cache, "clear"):
            await teams_cache.clear()

    slack_changed = _channel_enabled_changed(
        previous_channels=previous_channels,
        current_channels=current_channels,
        section="slack",
    )

    if slack_changed:
        slack_cache = getattr(request.app.state, "slack_runtime_cache", None)
        if slack_cache is not None and hasattr(slack_cache, "refresh"):
            await slack_cache.refresh()

    whatsapp_changed = _channel_enabled_changed(
        previous_channels=previous_channels,
        current_channels=current_channels,
        section="whatsapp",
    )

    if whatsapp_changed:
        whatsapp_cache = getattr(request.app.state, "whatsapp_runtime_cache", None)
        if whatsapp_cache is not None and hasattr(whatsapp_cache, "clear"):
            await whatsapp_cache.clear()



def _channel_enabled_changed(
    *,
    previous_channels: Mapping[str, Any] | None,
    current_channels: Mapping[str, Any] | None,
    section: str,
) -> bool:
    previous_enabled = _extract_enabled(previous_channels, section)
    current_enabled = _extract_enabled(current_channels, section)
    return previous_enabled != current_enabled


def _extract_section(
    channels: Mapping[str, Any] | None,
    section: str,
) -> dict[str, Any]:
    if not isinstance(channels, Mapping):
        return {}

    section_value = channels.get(section, {})
    if isinstance(section_value, Mapping):
        return dict(section_value)

    return {}


def _extract_enabled(
    channels: Mapping[str, Any] | None,
    section: str,
) -> bool:
    section_value = _extract_section(channels, section)
    enabled = section_value.get("enabled")

    if isinstance(enabled, (int, bool)):
        return bool(enabled)

    return False
