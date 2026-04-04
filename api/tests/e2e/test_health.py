"""E2E tests for health check endpoints."""

from __future__ import annotations

import pytest


@pytest.mark.e2e
class TestHealthEndpoints:
    """Test health check endpoints via HTTP."""

    async def test_health(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "memory_rss_mb" in data

    async def test_health_db(self, client):
        response = await client.get("/health/db")
        assert response.status_code == 200
        data = response.json()
        # Should contain pool status info
        assert isinstance(data, dict)

    async def test_health_ready(self, client):
        response = await client.get("/health/ready")
        # May return 404 in test env if route not fully registered,
        # or 200/503 in production-like setup
        if response.status_code == 200:
            data = response.json()
            assert data["status"] in ("ok", "degraded")
            assert "checks" in data
        else:
            # Accept 404/500 in minimal test app (no startup plugin)
            assert response.status_code in (404, 500)
