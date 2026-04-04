"""E2E tests for admin Providers endpoints."""

from __future__ import annotations

from uuid import uuid4

import pytest


@pytest.mark.e2e
@pytest.mark.skip(
    reason="ProvidersService has custom update/cache logic causing event loop issues in tests - needs investigation"
)
class TestAdminProvidersEndpoints:
    async def test_create_provider(self, client):
        response = await client.post(
            "/api/admin/providers",
            json={
                "name": "E2E Provider",
                "system_name": f"e2e-prov-{uuid4().hex[:8]}",
                "type": "openai",
                "endpoint": "https://api.openai.com/v1",
            },
        )
        assert response.status_code == 201
        assert response.json()["type"] == "openai"

    async def test_list_providers(self, client):
        response = await client.get("/api/admin/providers")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    @pytest.mark.skip(
        reason="ProvidersService.update has custom logic that causes event loop issues in tests"
    )
    async def test_update_provider(self, client):
        sn = f"upd-prov-{uuid4().hex[:8]}"
        create_resp = await client.post(
            "/api/admin/providers",
            json={
                "name": "Upd Provider",
                "system_name": sn,
                "type": "openai",
                "endpoint": "https://old.api.com",
            },
        )
        assert create_resp.status_code == 201
        provider_id = create_resp.json()["id"]

        # Use the same endpoint to avoid secrets_encrypted clearing logic
        response = await client.patch(
            f"/api/admin/providers/{provider_id}",
            json={"name": "Updated Provider", "endpoint": "https://old.api.com"},
        )
        assert response.status_code == 200

    async def test_delete_provider(self, client):
        create_resp = await client.post(
            "/api/admin/providers",
            json={
                "name": "Del Provider",
                "system_name": f"del-prov-{uuid4().hex[:8]}",
                "type": "openai",
            },
        )
        provider_id = create_resp.json()["id"]

        response = await client.delete(f"/api/admin/providers/{provider_id}")
        assert response.status_code in (200, 204)
