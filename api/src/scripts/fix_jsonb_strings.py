"""Fix double-encoded JSONB fields across all tables.

Some historical records have JSONB columns stored as JSON string literals
(e.g. '"[{...}]"' instead of '[{...}]'). This script finds and fixes them.

Usage:
    cd api/src && ../.venv/bin/python scripts/fix_jsonb_strings.py
    cd api/src && ../.venv/bin/python scripts/fix_jsonb_strings.py --dry-run
"""

import asyncio
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# All tables and their JSONB columns to check
JSONB_COLUMNS: dict[str, list[str]] = {
    "rag_tools": ["variants"],
    "retrieval_tools": ["variants"],
    "prompts": ["variants"],
    "agents": ["variants", "channels"],
    "ai_apps": ["settings", "tabs"],
    "ai_models": ["model_parameters", "parameters_metadata"],
    "collections": [
        "source_config",
        "chunking_config",
        "indexing_config",
        "metadata_config",
    ],
    "providers": ["model_config", "routing_config"],
    "api_servers": [
        "custom_headers",
        "security_scheme",
        "security_values",
        "tools",
    ],
    "mcp_servers": ["http_headers", "tools"],
    "evaluation_sets": ["items"],
    "evaluations": ["test_sets", "errors", "tool", "settings"],
    "jobs": ["definition"],
    "traces": ["cost_details", "extra_data", "spans"],
    "metrics": ["conversation_data", "extra_data", "x_attributes"],
    "knowledge_graphs": ["state", "settings"],
    "stored_files": ["extra"],
    "note_taker_jobs": ["result", "participants"],
    "note_taker_settings": ["config"],
}


async def fix_jsonb_strings(dry_run: bool = False) -> None:
    from core.config.app import settings

    engine = settings.db.get_engine()
    async with AsyncSession(engine) as session:
        total_fixed = 0
        for table, columns in JSONB_COLUMNS.items():
            for col in columns:
                try:
                    # Count corrupted records
                    count_result = await session.execute(
                        text(
                            f"SELECT count(*) FROM {table} "  # noqa: S608
                            f"WHERE {col} IS NOT NULL AND jsonb_typeof({col}) = 'string'"
                        )
                    )
                    count = count_result.scalar()
                    if not count:
                        continue

                    if dry_run:
                        print(f"  [DRY RUN] {table}.{col}: {count} corrupted records")
                        total_fixed += count
                        continue

                    # Fix: extract string content and re-parse as proper JSONB
                    result = await session.execute(
                        text(
                            f"UPDATE {table} "  # noqa: S608
                            f"SET {col} = ({col} #>> '{{}}')::jsonb "
                            f"WHERE {col} IS NOT NULL AND jsonb_typeof({col}) = 'string' "
                            f"RETURNING id"
                        )
                    )
                    rows = result.all()
                    if rows:
                        total_fixed += len(rows)
                        print(f"  Fixed {table}.{col}: {len(rows)} records")
                except Exception:
                    # Table or column might not exist in this DB
                    pass

        if not dry_run:
            await session.commit()

        if total_fixed == 0:
            print("All JSONB data is clean — no fixes needed.")
        else:
            action = "would fix" if dry_run else "fixed"
            print(f"\nTotal {action}: {total_fixed} records")

    await engine.dispose()


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("=== DRY RUN — no changes will be made ===\n")
    else:
        print("=== Fixing double-encoded JSONB fields ===\n")
    asyncio.run(fix_jsonb_strings(dry_run=dry_run))
