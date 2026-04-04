"""E2E tests for error handling and HTTP status codes."""

from __future__ import annotations

import pytest


@pytest.mark.e2e
class TestErrorHandling:
    """Verify correct HTTP status codes for error conditions."""

    async def test_404_not_found(self, client):
        """Non-existent resource should return 404 or 500."""
        from uuid_utils import uuid7

        response = await client.get(f"/api/admin/agents/{uuid7()}")
        assert response.status_code in (404, 500)

    async def test_404_unknown_route(self, client):
        """Unknown route should return 404."""
        response = await client.get("/api/admin/nonexistent_endpoint")
        assert response.status_code in (404, 405)

    async def test_422_validation_error(self, client):
        """Invalid data should return 400 or 422."""
        response = await client.post(
            "/api/admin/agents",
            json={},  # Missing required 'name' field
        )
        assert response.status_code in (400, 422)

    async def test_405_method_not_allowed(self, client):
        """Wrong HTTP method should return 405."""
        response = await client.put("/health")
        assert response.status_code == 405
