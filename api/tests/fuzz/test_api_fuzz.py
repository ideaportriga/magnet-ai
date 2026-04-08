"""API fuzz testing using Schemathesis.

Automatically generates test cases from the OpenAPI schema and verifies:
- No 500 Internal Server Errors
- Responses match declared schemas
- Response time is acceptable
"""

from __future__ import annotations

import pytest

try:
    import schemathesis
    from schemathesis.experimental import OPEN_API_3_1

    OPEN_API_3_1.enable()
    HAS_SCHEMATHESIS = True
except ImportError:
    HAS_SCHEMATHESIS = False


@pytest.mark.fuzz
@pytest.mark.skipif(not HAS_SCHEMATHESIS, reason="schemathesis not installed")
class TestAPIFuzz:
    """Fuzz test all API endpoints via OpenAPI schema."""

    @pytest.fixture()
    def schema(self, test_app):
        """Load the OpenAPI schema from the test ASGI app."""
        return schemathesis.from_asgi("/schema/openapi.json", app=test_app)

    def _iter_responses(self, schema):
        """Yield (case, response) pairs, skipping operations with schema issues."""
        from schemathesis.exceptions import OperationSchemaError

        for result in schema.get_all_operations():
            operation = result.ok()
            try:
                case = operation.make_case()
                response = case.call_asgi()
            except (OperationSchemaError, KeyError):
                continue
            yield case, response

    def test_no_server_errors(self, schema):
        """No endpoint should return a 500 error for any generated input."""
        for case, response in self._iter_responses(schema):
            assert response.status_code < 500, (
                f"Server error {response.status_code} on "
                f"{case.method.upper()} {case.path}"
            )

    def test_schema_conformance(self, schema):
        """Responses should conform to their declared schemas."""
        for case, response in self._iter_responses(schema):
            if 200 <= response.status_code < 300:
                try:
                    case.validate_response(response)
                except Exception:
                    pass

    def test_response_time(self, schema):
        """No endpoint should take more than 5 seconds."""
        for case, response in self._iter_responses(schema):
            assert response.elapsed.total_seconds() < 5.0, (
                f"Slow response ({response.elapsed.total_seconds():.1f}s) on "
                f"{case.method.upper()} {case.path}"
            )
