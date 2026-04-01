"""Locust load-test scenarios for Magnet AI API.

Run:
    locust -f api/tests/load/locustfile.py --host http://localhost:8000

Scenarios
---------
1. HealthCheck         — baseline throughput (no DB)
2. DBHealth            — connection pool pressure
3. AgentsList          — auth + DB query + serialisation
4. ConcurrentUploads   — memory pressure via file uploads
5. MixedWorkload       — realistic traffic distribution
"""

from __future__ import annotations

import io
import os

from locust import HttpUser, between, task


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

API_KEY = os.environ.get("LOAD_TEST_API_KEY", "")
AUTH_HEADERS: dict[str, str] = {}
if API_KEY:
    AUTH_HEADERS["x-api-key"] = API_KEY


# ---------------------------------------------------------------------------
# Scenario 1 & 2: Health checks (baseline)
# ---------------------------------------------------------------------------


class HealthCheckUser(HttpUser):
    """Pure health-check traffic — measures baseline latency without DB."""

    wait_time = between(0.1, 0.5)
    weight = 5

    @task
    def health(self) -> None:
        self.client.get("/health")


class DBHealthUser(HttpUser):
    """Hits /health/db to exercise the connection pool checkout path."""

    wait_time = between(0.5, 1)
    weight = 3

    @task
    def db_health(self) -> None:
        self.client.get("/health/db")


# ---------------------------------------------------------------------------
# Scenario 3: Authenticated API list endpoints
# ---------------------------------------------------------------------------


class AgentsListUser(HttpUser):
    """Fetches agent list — requires auth + DB read + JSON serialisation."""

    wait_time = between(1, 3)
    weight = 4

    @task(3)
    def list_agents(self) -> None:
        self.client.get("/api/sql_agents", headers=AUTH_HEADERS)

    @task(2)
    def list_ai_models(self) -> None:
        self.client.get("/api/ai_models", headers=AUTH_HEADERS)

    @task(1)
    def list_prompts(self) -> None:
        self.client.get("/api/prompts", headers=AUTH_HEADERS)


# ---------------------------------------------------------------------------
# Scenario 4: File upload memory pressure
# ---------------------------------------------------------------------------


class UploadUser(HttpUser):
    """Uploads files to test memory behaviour under concurrent load.

    Set env LOAD_TEST_UPLOAD_ENDPOINT to the actual upload path.
    Default is a placeholder that will return 404 if not configured.
    """

    wait_time = between(5, 15)
    weight = 1

    UPLOAD_ENDPOINT = os.environ.get(
        "LOAD_TEST_UPLOAD_ENDPOINT", "/api/knowledge_sources/upload"
    )
    FILE_SIZE_MB = int(os.environ.get("LOAD_TEST_FILE_SIZE_MB", "5"))

    @task
    def upload_file(self) -> None:
        payload = io.BytesIO(b"x" * (self.FILE_SIZE_MB * 1024 * 1024))
        self.client.post(
            self.UPLOAD_ENDPOINT,
            files={"data": ("test.bin", payload, "application/octet-stream")},
            headers=AUTH_HEADERS,
        )


# ---------------------------------------------------------------------------
# Scenario 5: Mixed realistic workload (default entry point)
# ---------------------------------------------------------------------------


class MixedWorkloadUser(HttpUser):
    """Simulates realistic traffic: mostly reads, occasional writes."""

    wait_time = between(1, 5)
    weight = 10

    @task(10)
    def health(self) -> None:
        self.client.get("/health")

    @task(5)
    def db_health(self) -> None:
        self.client.get("/health/db")

    @task(8)
    def list_agents(self) -> None:
        self.client.get("/api/sql_agents", headers=AUTH_HEADERS)

    @task(3)
    def list_collections(self) -> None:
        self.client.get("/api/collections", headers=AUTH_HEADERS)

    @task(2)
    def list_ai_apps(self) -> None:
        self.client.get("/api/ai_apps", headers=AUTH_HEADERS)
