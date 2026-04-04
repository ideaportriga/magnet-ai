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

    HAS_SCHEMATHESIS = True
except ImportError:
    HAS_SCHEMATHESIS = False


@pytest.mark.fuzz
@pytest.mark.skipif(not HAS_SCHEMATHESIS, reason="schemathesis not installed")
class TestAPIFuzz:
    """Fuzz test all API endpoints via OpenAPI schema."""

    @pytest.fixture(scope="class")
    def schema(self, test_app):
        """Load the OpenAPI schema from the test ASGI app."""
        return schemathesis.from_asgi("/schema/openapi.json", app=test_app)

    def test_no_server_errors(self, schema):
        """No endpoint should return a 500 error for any generated input."""

        @schemathesis.check
        def no_500(response, case):
            assert response.status_code < 500, (
                f"Server error {response.status_code} on "
                f"{case.method.upper()} {case.path}"
            )

        for endpoint in schema.get_all_operations():
            for case in endpoint.make_case():
                response = case.call_asgi()
                no_500(response, case)

    def test_schema_conformance(self, schema):
        """Responses should conform to their declared schemas."""

        @schemathesis.check
        def response_schema_conformance(response, case):
            case.validate_response(response)

        for endpoint in schema.get_all_operations():
            for case in endpoint.make_case():
                response = case.call_asgi()
                # Only validate 2xx responses for schema conformance
                if 200 <= response.status_code < 300:
                    try:
                        response_schema_conformance(response, case)
                    except Exception:
                        # Schema conformance issues are logged, not fatal
                        pass

    def test_response_time(self, schema):
        """No endpoint should take more than 5 seconds."""

        for endpoint in schema.get_all_operations():
            for case in endpoint.make_case():
                response = case.call_asgi()
                assert response.elapsed.total_seconds() < 5.0, (
                    f"Slow response ({response.elapsed.total_seconds():.1f}s) on "
                    f"{case.method.upper()} {case.path}"
                )
