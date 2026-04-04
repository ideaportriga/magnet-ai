"""E2E tests for admin Collections endpoints."""

from __future__ import annotations

from uuid import uuid4

import pytest


@pytest.mark.e2e
class TestAdminCollectionsEndpoints:
    async def test_create_collection(self, client):
        response = await client.post(
            "/api/admin/sql_collections",
            json={
                "name": "E2E Collection",
                "system_name": f"e2e-coll-{uuid4().hex[:8]}",
                "type": "documents",
            },
        )
        assert response.status_code == 201

    async def test_list_collections(self, client):
        response = await client.get("/api/admin/sql_collections")
        assert response.status_code == 200
        assert "items" in response.json()

    async def test_get_collection_by_id(self, client):
        create_resp = await client.post(
            "/api/admin/sql_collections",
            json={
                "name": "Get Coll",
                "system_name": f"get-coll-{uuid4().hex[:8]}",
            },
        )
        coll_id = create_resp.json()["id"]

        response = await client.get(f"/api/admin/sql_collections/{coll_id}")
        assert response.status_code == 200

    async def test_delete_collection(self, client):
        create_resp = await client.post(
            "/api/admin/sql_collections",
            json={
                "name": "Del Coll",
                "system_name": f"del-coll-{uuid4().hex[:8]}",
            },
        )
        coll_id = create_resp.json()["id"]

        response = await client.delete(f"/api/admin/sql_collections/{coll_id}")
        assert response.status_code in (200, 204)
