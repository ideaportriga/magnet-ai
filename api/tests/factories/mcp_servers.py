"""MCP Server factories."""

from __future__ import annotations

import factory

from core.db.models.mcp_server import MCPServer

from .base import BaseFactory
from .users import _resolve_default_tenant_id


class MCPServerFactory(BaseFactory):
    class Meta:
        model = MCPServer

    name = factory.Sequence(lambda n: f"MCP Server {n}")
    system_name = factory.Sequence(lambda n: f"mcp-server-{n}")
    transport = "sse"
    url = factory.Sequence(lambda n: f"http://localhost:900{n}")
    headers = factory.LazyFunction(dict)
    tools = factory.LazyFunction(list)
    # PR 10 #7: mcp_servers are tenant-scoped; default to the seeded `default` tenant.
    tenant_id = factory.LazyFunction(_resolve_default_tenant_id)
