"""E2E tests for admin Agents endpoints."""

from __future__ import annotations

from uuid import uuid4

import pytest


@pytest.mark.e2e
class TestAdminAgentsEndpoints:
    """CRUD operations on /api/admin/agents via HTTP."""

    async def test_create_agent(self, client):
        response = await client.post(
            "/api/admin/agents",
            json={
                "name": "E2E Agent",
                "system_name": f"e2e-agent-{uuid4().hex[:8]}",
                "description": "Created via E2E test",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "E2E Agent"
        assert "id" in data

    async def test_list_agents(self, client):
        response = await client.get("/api/admin/agents")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    async def test_get_agent_by_id(self, client):
        # Create first
        create_resp = await client.post(
            "/api/admin/agents",
            json={
                "name": "Get Agent",
                "system_name": f"get-agent-{uuid4().hex[:8]}",
            },
        )
        assert create_resp.status_code == 201
        agent_id = create_resp.json()["id"]

        # Get
        response = await client.get(f"/api/admin/agents/{agent_id}")
        assert response.status_code == 200
        assert response.json()["id"] == agent_id

    async def test_update_agent(self, client):
        # Create
        create_resp = await client.post(
            "/api/admin/agents",
            json={
                "name": "Old Name",
                "system_name": f"upd-agent-{uuid4().hex[:8]}",
            },
        )
        agent_id = create_resp.json()["id"]

        # Update
        response = await client.patch(
            f"/api/admin/agents/{agent_id}",
            json={"name": "New Name"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "New Name"

    async def test_delete_agent(self, client):
        # Create
        create_resp = await client.post(
            "/api/admin/agents",
            json={
                "name": "Del Agent",
                "system_name": f"del-agent-{uuid4().hex[:8]}",
            },
        )
        agent_id = create_resp.json()["id"]

        # Delete
        response = await client.delete(f"/api/admin/agents/{agent_id}")
        assert response.status_code in (200, 204, 404)

    async def test_get_agent_not_found(self, client):
        from uuid_utils import uuid7

        response = await client.get(f"/api/admin/agents/{uuid7()}")
        assert response.status_code in (404, 500)

    async def test_get_agent_by_code(self, client):
        sn = f"code-agent-{uuid4().hex[:8]}"
        await client.post(
            "/api/admin/agents",
            json={"name": "Code Agent", "system_name": sn},
        )
        response = await client.get(f"/api/admin/agents/code/{sn}")
        assert response.status_code == 200
        assert response.json()["system_name"] == sn
