"""MCP tools exposed to remote clients.

Tools are registered onto the FastMCP instance in `server.py`. Each tool is a
plain async function — FastMCP introspects its type hints and docstring to
generate the input schema and tool description that clients see.
"""

from __future__ import annotations

__all__: list[str] = []
