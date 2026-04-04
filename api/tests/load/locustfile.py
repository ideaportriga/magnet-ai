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
6. CRUDStorm           — concurrent create/update/delete
7. SearchUser          — list endpoints with filters (simulates search)
8. AgentExecution      — agent test endpoint under load
9. BulkOperations      — batch CRUD operations
10. ConcurrentWrite    — same-resource writes to detect DB locks
"""

from __future__ import annotations

import io
import os
import random
import string

from locust import HttpUser, between, task


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

API_KEY = os.environ.get("LOAD_TEST_API_KEY", "")
AUTH_HEADERS: dict[str, str] = {}
if API_KEY:
    AUTH_HEADERS["x-api-key"] = API_KEY


def _random_name(prefix: str = "load") -> str:
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


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
        self.client.get("/api/admin/sql_agents", headers=AUTH_HEADERS)

    @task(2)
    def list_ai_models(self) -> None:
        self.client.get("/api/admin/ai_models", headers=AUTH_HEADERS)

    @task(1)
    def list_prompts(self) -> None:
        self.client.get("/api/admin/prompt_templates", headers=AUTH_HEADERS)


# ---------------------------------------------------------------------------
# Scenario 4: File upload memory pressure
# ---------------------------------------------------------------------------


class UploadUser(HttpUser):
    """Uploads files to test memory behaviour under concurrent load."""

    wait_time = between(5, 15)
    weight = 1

    UPLOAD_ENDPOINT = os.environ.get(
        "LOAD_TEST_UPLOAD_ENDPOINT", "/api/admin/knowledge_sources/upload"
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
        self.client.get("/api/admin/sql_agents", headers=AUTH_HEADERS)

    @task(3)
    def list_collections(self) -> None:
        self.client.get("/api/admin/sql_collections", headers=AUTH_HEADERS)

    @task(2)
    def list_ai_apps(self) -> None:
        self.client.get("/api/admin/ai_apps", headers=AUTH_HEADERS)


# ---------------------------------------------------------------------------
# Scenario 6: CRUD Storm — concurrent create/update/delete
# ---------------------------------------------------------------------------


class CRUDStormUser(HttpUser):
    """Rapidly creates, updates, and deletes agents to stress DB writes."""

    wait_time = between(0.5, 2)
    weight = 8

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._created_ids: list[str] = []

    @task(5)
    def create_agent(self) -> None:
        name = _random_name("storm")
        resp = self.client.post(
            "/api/admin/sql_agents",
            json={"name": name, "system_name": name},
            headers=AUTH_HEADERS,
        )
        if resp.status_code == 201:
            self._created_ids.append(resp.json().get("id", ""))

    @task(3)
    def update_agent(self) -> None:
        if not self._created_ids:
            return
        agent_id = random.choice(self._created_ids)
        self.client.patch(
            f"/api/admin/sql_agents/{agent_id}",
            json={"description": f"Updated at {random.randint(0, 99999)}"},
            headers=AUTH_HEADERS,
        )

    @task(2)
    def delete_agent(self) -> None:
        if not self._created_ids:
            return
        agent_id = self._created_ids.pop(random.randrange(len(self._created_ids)))
        self.client.delete(
            f"/api/admin/sql_agents/{agent_id}",
            headers=AUTH_HEADERS,
        )


# ---------------------------------------------------------------------------
# Scenario 7: Search / Filter — list endpoints with query params
# ---------------------------------------------------------------------------


class SearchUser(HttpUser):
    """Exercises list endpoints with pagination and search filters."""

    wait_time = between(1, 3)
    weight = 8

    @task(4)
    def search_agents(self) -> None:
        self.client.get(
            "/api/admin/sql_agents",
            params={"search": "test", "limit": 10, "offset": 0},
            headers=AUTH_HEADERS,
        )

    @task(3)
    def paginate_agents(self) -> None:
        offset = random.randint(0, 50)
        self.client.get(
            "/api/admin/sql_agents",
            params={"limit": 20, "offset": offset},
            headers=AUTH_HEADERS,
        )

    @task(2)
    def search_collections(self) -> None:
        self.client.get(
            "/api/admin/sql_collections",
            params={"search": "doc", "limit": 10},
            headers=AUTH_HEADERS,
        )

    @task(1)
    def search_prompts(self) -> None:
        self.client.get(
            "/api/admin/prompt_templates",
            params={"search": "hello", "limit": 5},
            headers=AUTH_HEADERS,
        )


# ---------------------------------------------------------------------------
# Scenario 8: Bulk Operations
# ---------------------------------------------------------------------------


class BulkOperationsUser(HttpUser):
    """Creates multiple resources in rapid succession."""

    wait_time = between(2, 5)
    weight = 3

    @task
    def bulk_create_agents(self) -> None:
        for _ in range(5):
            name = _random_name("bulk")
            self.client.post(
                "/api/admin/sql_agents",
                json={"name": name, "system_name": name},
                headers=AUTH_HEADERS,
            )

    @task
    def bulk_create_prompts(self) -> None:
        for _ in range(3):
            name = _random_name("bulk-prompt")
            self.client.post(
                "/api/admin/prompt_templates",
                json={
                    "name": name,
                    "system_name": name,
                    "active_variant": "default",
                    "variants": [{"name": "default", "template": "Test template"}],
                },
                headers=AUTH_HEADERS,
            )


# ---------------------------------------------------------------------------
# Scenario 9: Concurrent Writes — same resource updates to detect locks
# ---------------------------------------------------------------------------


class ConcurrentWriteUser(HttpUser):
    """Multiple users updating the same resource to detect DB lock contention."""

    wait_time = between(0.1, 0.5)
    weight = 6

    SHARED_AGENT_NAME = os.environ.get("LOAD_TEST_SHARED_AGENT", "")

    def on_start(self):
        """Create a shared agent on first request if not exists."""
        if not self.SHARED_AGENT_NAME:
            return
        # Try to create — if it already exists, that's OK
        self.client.post(
            "/api/admin/sql_agents",
            json={
                "name": self.SHARED_AGENT_NAME,
                "system_name": self.SHARED_AGENT_NAME,
            },
            headers=AUTH_HEADERS,
        )

    @task
    def update_shared_agent(self) -> None:
        if not self.SHARED_AGENT_NAME:
            return
        # Get by code to find the ID
        resp = self.client.get(
            f"/api/admin/sql_agents/code/{self.SHARED_AGENT_NAME}",
            headers=AUTH_HEADERS,
        )
        if resp.status_code != 200:
            return
        agent_id = resp.json().get("id")
        if not agent_id:
            return

        self.client.patch(
            f"/api/admin/sql_agents/{agent_id}",
            json={
                "description": f"Concurrent update {random.randint(0, 99999)}",
                "category": random.choice(["cat-a", "cat-b", "cat-c"]),
            },
            headers=AUTH_HEADERS,
        )
