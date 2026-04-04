"""E2E tests for OpenAPI schema endpoint."""

from __future__ import annotations

import pytest


@pytest.mark.e2e
class TestOpenAPI:
    """Verify the OpenAPI schema is served correctly."""

    async def test_openapi_json(self, client):
        """OpenAPI schema should be valid JSON."""
        response = await client.get("/schema/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "paths" in schema
        assert "info" in schema

    async def test_openapi_has_health_paths(self, client):
        """Schema should include health check paths."""
        response = await client.get("/schema/openapi.json")
        paths = response.json()["paths"]
        assert "/health" in paths

    async def test_openapi_has_admin_paths(self, client):
        """Schema should include admin CRUD paths."""
        response = await client.get("/schema/openapi.json")
        paths = response.json()["paths"]
        # At least some admin paths should exist
        admin_paths = [p for p in paths if "/admin/" in p or "/api/" in p]
        assert len(admin_paths) > 0
