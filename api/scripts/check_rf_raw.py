#!/usr/bin/env python3
"""Check raw variant data for templates with response_format errors."""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import logging

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

from core.config.app import alchemy  # noqa: E402
from sqlalchemy import text  # noqa: E402


ERROR_TEMPLATES = [
    "DEFAULT_DEEP_RESEARCH_ANALYZE_SEARCH_RESULTS",
    "LIAA_REASONING_PROMPT",
    "MF_AIRLINE_CASE_CLASSIFICATION",
    "STT_TRANSCRIPT_POSTPROCESSING",
]


async def main():
    async with alchemy.get_session() as session:
        for name in ERROR_TEMPLATES:
            r = await session.execute(
                text("""
                SELECT system_name, 
                       jsonb_typeof(variants) as variants_type,
                       jsonb_array_length(variants) as variant_count,
                       variants->0->>'variantName' as first_variant_name,
                       variants->0->>'isActive' as first_active,
                       variants->0->'responseFormat' as response_format_raw,
                       jsonb_typeof(variants->0->'responseFormat') as rf_type
                FROM prompts
                WHERE system_name = :name
            """),
                {"name": name},
            )
            row = r.fetchone()
            if not row:
                print(f"\n{name}: NOT FOUND")
                continue

            print(f"\n{'=' * 80}")
            print(f"TEMPLATE: {name}")
            print(f"  variants_type={row.variants_type}, count={row.variant_count}")
            print(
                f"  first_variant: name={row.first_variant_name}, active={row.first_active}"
            )
            print(f"  rf_type={row.rf_type}")

            if row.response_format_raw:
                rf = (
                    json.loads(row.response_format_raw)
                    if isinstance(row.response_format_raw, str)
                    else row.response_format_raw
                )
                formatted = json.dumps(rf, indent=2, ensure_ascii=False)
                # Truncate for readability
                if len(formatted) > 2000:
                    formatted = formatted[:2000] + "\n... (truncated)"
                print(f"  response_format:\n{formatted}")
            else:
                print("  response_format: NULL/None")

            # Also check ALL variants for responseFormat
            r2 = await session.execute(
                text("""
                SELECT v->>'variantName' as vname, 
                       v->>'isActive' as is_active,
                       jsonb_typeof(v->'responseFormat') as rf_type,
                       LEFT(v->>'responseFormat', 100) as rf_preview
                FROM prompts p, jsonb_array_elements(p.variants) v
                WHERE p.system_name = :name
            """),
                {"name": name},
            )
            rows2 = r2.fetchall()
            print("\n  All variants:")
            for v in rows2:
                print(
                    f"    {v.vname}: active={v.is_active}, rf_type={v.rf_type}, rf_preview={v.rf_preview}"
                )


asyncio.run(main())
