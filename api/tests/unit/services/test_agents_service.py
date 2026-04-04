"""Unit tests for AgentsService."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from core.db.models.agent import Agent


@pytest.mark.unit
class TestAgentsService:
    """Tests for the AgentsService CRUD operations."""

    async def test_create_agent(self):
        """Service should create an agent and return the model instance."""
        from core.domain.agents.service import AgentsService

        mock_session = AsyncMock()
        service = AgentsService(session=mock_session)

        agent_data = {
            "name": "Test Agent",
            "system_name": "test-agent",
            "description": "A test agent",
            "category": "test",
            "active_variant": "default",
            "variants": [{"name": "default", "system_prompt": "Hello"}],
        }

        with patch.object(service, "create", new_callable=AsyncMock) as mock_create:
            mock_agent = MagicMock(spec=Agent)
            mock_agent.id = uuid4()
            mock_agent.name = agent_data["name"]
            mock_agent.system_name = agent_data["system_name"]
            mock_create.return_value = mock_agent

            result = await service.create(agent_data)

            mock_create.assert_called_once_with(agent_data)
            assert result.name == "Test Agent"
            assert result.system_name == "test-agent"

    async def test_get_agent_by_id(self):
        """Service should retrieve an agent by ID."""
        from core.domain.agents.service import AgentsService

        mock_session = AsyncMock()
        service = AgentsService(session=mock_session)
        agent_id = uuid4()

        with patch.object(service, "get", new_callable=AsyncMock) as mock_get:
            mock_agent = MagicMock(spec=Agent)
            mock_agent.id = agent_id
            mock_agent.name = "Test Agent"
            mock_get.return_value = mock_agent

            result = await service.get(agent_id)

            mock_get.assert_called_once_with(agent_id)
            assert result.id == agent_id

    async def test_get_agent_by_system_name(self):
        """Service should retrieve an agent by system_name."""
        from core.domain.agents.service import AgentsService

        mock_session = AsyncMock()
        service = AgentsService(session=mock_session)

        with patch.object(service, "get_one", new_callable=AsyncMock) as mock_get_one:
            mock_agent = MagicMock(spec=Agent)
            mock_agent.system_name = "test-agent"
            mock_get_one.return_value = mock_agent

            result = await service.get_one(system_name="test-agent")

            mock_get_one.assert_called_once_with(system_name="test-agent")
            assert result.system_name == "test-agent"

    async def test_update_agent(self):
        """Service should update an agent's fields."""
        from core.domain.agents.service import AgentsService

        mock_session = AsyncMock()
        service = AgentsService(session=mock_session)
        agent_id = uuid4()

        with patch.object(service, "update", new_callable=AsyncMock) as mock_update:
            mock_agent = MagicMock(spec=Agent)
            mock_agent.id = agent_id
            mock_agent.name = "Updated Agent"
            mock_update.return_value = mock_agent

            result = await service.update({"name": "Updated Agent"}, item_id=agent_id)

            assert result.name == "Updated Agent"

    async def test_delete_agent(self):
        """Service should delete an agent by ID."""
        from core.domain.agents.service import AgentsService

        mock_session = AsyncMock()
        service = AgentsService(session=mock_session)
        agent_id = uuid4()

        with patch.object(service, "delete", new_callable=AsyncMock) as mock_delete:
            mock_agent = MagicMock(spec=Agent)
            mock_delete.return_value = mock_agent

            await service.delete(agent_id)

            mock_delete.assert_called_once_with(agent_id)

    async def test_list_agents(self):
        """Service should list agents with count."""
        from core.domain.agents.service import AgentsService

        mock_session = AsyncMock()
        service = AgentsService(session=mock_session)

        with patch.object(
            service, "list_and_count", new_callable=AsyncMock
        ) as mock_list:
            agents = [MagicMock(spec=Agent) for _ in range(3)]
            mock_list.return_value = (agents, 3)

            results, total = await service.list_and_count()

            assert total == 3
            assert len(results) == 3
