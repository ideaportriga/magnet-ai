#!/usr/bin/env python3
"""Inspect actual variant JSON keys in prompts table."""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import logging

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

from core.config.app import alchemy  # noqa: E402
from sqlalchemy import text  # noqa: E402


async def main():
    async with alchemy.get_session() as session:
        # 1. Get the actual JSON keys in variants for a template
        r = await session.execute(
            text("""
            SELECT p.system_name, jsonb_object_keys(v) as key
            FROM prompts p, jsonb_array_elements(p.variants) v
            WHERE p.system_name = 'DEFAULT_DEEP_RESEARCH_ANALYZE_SEARCH_RESULTS'
            LIMIT 50
        """)
        )
        rows = r.fetchall()
        print("Keys in variant for DEFAULT_DEEP_RESEARCH_ANALYZE_SEARCH_RESULTS:")
        for row in rows:
            print(f"  {row.key}")

        # 2. Check the raw variant JSON
        r = await session.execute(
            text("""
            SELECT variants->0 as v0
            FROM prompts
            WHERE system_name = 'DEFAULT_DEEP_RESEARCH_ANALYZE_SEARCH_RESULTS'
        """)
        )
        row = r.fetchone()
        if row and row.v0:
            v = row.v0 if isinstance(row.v0, dict) else json.loads(row.v0)
            print(f"\nFull variant keys: {list(v.keys())}")
            # Show response format related keys
            for k in v.keys():
                if (
                    "response" in k.lower()
                    or "format" in k.lower()
                    or "schema" in k.lower()
                ):
                    val = v[k]
                    if isinstance(val, str) and len(val) > 300:
                        val = val[:300] + "..."
                    elif isinstance(val, dict):
                        val = json.dumps(val, indent=2)[:500]
                    print(f"\n  {k} = {val}")

        # 3. Let's also check transform_to_flat to understand key mapping
        r = await session.execute(
            text("""
            SELECT p.system_name,
                   v->>'response_format' as rf1,
                   v->>'responseFormat' as rf2,
                   v->'response_format' as rf3,
                   v->'responseFormat' as rf4,
                   v->>'output_schema' as os1,
                   v->>'outputSchema' as os2,
                   v->'output_schema' as os3,
                   v->'outputSchema' as os4
            FROM prompts p, jsonb_array_elements(p.variants) v
            WHERE p.system_name = 'DEFAULT_DEEP_RESEARCH_ANALYZE_SEARCH_RESULTS'
            LIMIT 1
        """)
        )
        row = r.fetchone()
        print("\n\nChecking various field name patterns:")
        print(f"  response_format (text): {row.rf1}")
        print(f"  responseFormat (text): {row.rf2}")
        print(f"  response_format (json): {row.rf3}")
        print(f"  responseFormat (json): {row.rf4}")
        print(f"  output_schema (text): {row.os1}")
        print(f"  outputSchema (text): {row.os2}")
        print(f"  output_schema (json): {row.os3}")
        print(f"  outputSchema (json): {row.os4}")


asyncio.run(main())
