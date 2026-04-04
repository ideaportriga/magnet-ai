"""Integration tests for MCP Servers CRUD."""

from __future__ import annotations

from uuid import uuid4

import pytest

from core.domain.mcp_servers.service import MCPServersService


@pytest.mark.integration
class TestMCPServersCRUD:
    async def test_create_mcp_server(self, db_session):
        service = MCPServersService(session=db_session)
        obj = await service.create(
            {
                "name": "Test MCP",
                "system_name": f"mcp-{uuid4().hex[:8]}",
                "transport": "sse",
                "url": "http://localhost:9000",
                "tools": [{"name": "search", "description": "Search tool"}],
            }
        )
        assert obj.id is not None
        assert obj.transport == "sse"

    async def test_read_mcp_server(self, db_session):
        service = MCPServersService(session=db_session)
        sn = f"mcp-{uuid4().hex[:8]}"
        created = await service.create(
            {"name": "Read MCP", "system_name": sn, "transport": "stdio", "url": "cmd"}
        )
        fetched = await service.get(created.id)
        assert fetched.system_name == sn

    async def test_update_mcp_server(self, db_session):
        service = MCPServersService(session=db_session)
        created = await service.create(
            {
                "name": "Old MCP",
                "system_name": f"mcp-{uuid4().hex[:8]}",
                "transport": "sse",
                "url": "http://old:9000",
            }
        )
        updated = await service.update({"url": "http://new:9000"}, item_id=created.id)
        assert updated.url == "http://new:9000"

    async def test_jsonb_tools(self, db_session):
        """Tools JSONB should round-trip."""
        service = MCPServersService(session=db_session)
        tools = [
            {
                "name": "tool1",
                "description": "First",
                "inputSchema": {"type": "object"},
            },
            {"name": "tool2", "description": "Second"},
        ]
        created = await service.create(
            {
                "name": "Tools MCP",
                "system_name": f"mcp-{uuid4().hex[:8]}",
                "transport": "sse",
                "url": "http://localhost:9001",
                "tools": tools,
            }
        )
        fetched = await service.get(created.id)
        assert len(fetched.tools) == 2

    async def test_delete_mcp_server(self, db_session):
        service = MCPServersService(session=db_session)
        created = await service.create(
            {
                "name": "Del MCP",
                "system_name": f"mcp-{uuid4().hex[:8]}",
                "transport": "sse",
                "url": "http://del:9000",
            }
        )
        await service.delete(created.id)
        with pytest.raises(Exception):
            await service.get(created.id)
