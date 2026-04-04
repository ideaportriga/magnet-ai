"""Schemathesis fuzz testing configuration."""

from __future__ import annotations


import pytest


@pytest.fixture(scope="session")
def openapi_schema_url():
    """URL of the OpenAPI schema for fuzz testing."""
    return "/schema/openapi.json"
