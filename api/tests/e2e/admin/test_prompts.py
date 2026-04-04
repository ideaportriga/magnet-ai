"""E2E tests for admin Prompts endpoints."""

from __future__ import annotations

from uuid import uuid4

import pytest


@pytest.mark.e2e
class TestAdminPromptsEndpoints:
    async def test_create_prompt(self, client):
        response = await client.post(
            "/api/admin/prompt_templates",
            json={
                "name": "E2E Prompt",
                "system_name": f"e2e-prompt-{uuid4().hex[:8]}",
            },
        )
        assert response.status_code == 201

    async def test_list_prompts(self, client):
        response = await client.get("/api/admin/prompt_templates")
        assert response.status_code == 200
        assert "items" in response.json()

    async def test_update_prompt(self, client):
        create_resp = await client.post(
            "/api/admin/prompt_templates",
            json={
                "name": "Upd Prompt",
                "system_name": f"upd-prompt-{uuid4().hex[:8]}",
            },
        )
        prompt_id = create_resp.json()["id"]

        response = await client.patch(
            f"/api/admin/prompt_templates/{prompt_id}",
            json={"name": "Updated Prompt"},
        )
        assert response.status_code == 200

    async def test_delete_prompt(self, client):
        create_resp = await client.post(
            "/api/admin/prompt_templates",
            json={
                "name": "Del Prompt",
                "system_name": f"del-prompt-{uuid4().hex[:8]}",
            },
        )
        prompt_id = create_resp.json()["id"]

        response = await client.delete(f"/api/admin/prompt_templates/{prompt_id}")
        assert response.status_code in (200, 204)
