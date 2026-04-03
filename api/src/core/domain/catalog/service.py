from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

ENTITY_TABLES = [
    ("agents", "agents", "Agent"),
    ("ai_apps", "ai_apps", "AI App"),
    ("promptTemplates", "prompts", "Prompt Template"),
    ("rag_tools", "rag_tools", "RAG Tool"),
    ("retrieval", "retrieval_tools", "Retrieval Tool"),
    ("collections", "collections", "Knowledge Source"),
    ("model", "ai_models", "Model"),
    ("provider", "providers", "Model Provider"),
    ("evaluation_sets", "evaluation_sets", "Test Set"),
    ("mcp_servers", "mcp_servers", "MCP Server"),
    ("knowledge_graph", "knowledge_graphs", "Knowledge Graph"),
    ("api_servers", "api_servers", "API Server"),
]

# Extra columns per entity type (beyond the base set).
# Each value is a dict of {output_alias: sql_expression}.
_EXTRA_COLUMNS: dict[str, dict[str, str]] = {
    "model": {
        "display_name": "display_name",
        "type": "type",
        "parent_system_name": "provider_system_name",
    },
    "provider": {
        "category": "category",
    },
}

_OPTIONAL_FIELDS = ("display_name", "type", "category", "parent_system_name")


def _build_catalog_query() -> str:
    parts = []
    for entity_type, table, _label in ENTITY_TABLES:
        extras = _EXTRA_COLUMNS.get(entity_type, {})
        extra_cols = ", ".join(
            f"{extras[f]} as {f}" if f in extras else f"NULL as {f}"
            for f in _OPTIONAL_FIELDS
        )
        parts.append(
            f"SELECT id::text, name, system_name, "
            f"COALESCE(description, '') as description, "
            f"'{entity_type}' as entity_type, "
            f"updated_at, {extra_cols} "
            f"FROM {table}"
        )
    return " UNION ALL ".join(parts) + " ORDER BY updated_at DESC NULLS LAST"


ENTITY_LABEL_MAP = {et: label for et, _table, label in ENTITY_TABLES}


async def get_catalog(db_session: AsyncSession) -> list[dict]:
    sql = _build_catalog_query()
    result = await db_session.execute(text(sql))
    rows = result.mappings().all()
    return [
        {
            **dict(row),
            "entity_label": ENTITY_LABEL_MAP.get(
                row["entity_type"], row["entity_type"]
            ),
        }
        for row in rows
    ]
