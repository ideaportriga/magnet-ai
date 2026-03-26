"""Test utility endpoints for e2e testing.

Provides access to the in-memory error collector.
Only registered when DEBUG_MODE=True. Never expose in production.
"""

from litestar import Controller, get, post

from core.server.test_error_collector import get_collector


class TestUtilsController(Controller):
    path = "/test"
    tags = ["test-utils"]

    @get("/errors", exclude_from_auth=True)
    async def get_errors(self) -> list[dict]:
        """Return all collected backend errors since last reset."""
        return get_collector().get_all()

    @post("/errors/reset", exclude_from_auth=True)
    async def reset_errors(self) -> None:
        """Clear the collected errors. Call before each test."""
        get_collector().reset()
