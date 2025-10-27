from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from advanced_alchemy.extensions.litestar import filters, providers, service
from litestar import Controller, delete, get, patch, post
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
        self, agents_service: AgentsService, data: AgentCreate
    ) -> Agent:
        """Create a new agent."""
        obj = await agents_service.create(data)
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
        agent_id: UUID = Parameter(
            title="Agent ID",
            description="The agent to update.",
        ),
    ) -> Agent:
        """Update an agent."""
        obj = await agents_service.update(data, item_id=agent_id, auto_commit=True)
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
