#!/usr/bin/env python3
"""Deep analysis of all error categories in traces."""

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
        # ── 1. response_format schema errors — what exactly is wrong? ──
        print("=" * 80)
        print("1. RESPONSE_FORMAT SCHEMA ERRORS")
        print("=" * 80)
        r = await session.execute(
            text("""
            SELECT DISTINCT LEFT(s->>'status_message', 400) as msg
            FROM traces t, jsonb_array_elements(t.spans) s
            WHERE t.start_time >= '2026-03-05'
              AND s->>'status' = 'error'
              AND s->>'status_message' LIKE '%Invalid schema for response_format%'
            LIMIT 20
        """)
        )
        rows = r.fetchall()
        print(f"Found {len(rows)} unique error messages:\n")
        for i, row in enumerate(rows, 1):
            print(f"  [{i}] {row.msg}\n")

        # ── 2. max_tokens errors — which models? ──
        print("=" * 80)
        print("2. MAX_TOKENS ERRORS — which models?")
        print("=" * 80)
        r = await session.execute(
            text("""
            SELECT 
                s->>'attributes' as attrs,
                LEFT(s->>'status_message', 200) as msg
            FROM traces t, jsonb_array_elements(t.spans) s
            WHERE t.start_time >= '2026-03-05'
              AND s->>'status' = 'error'
              AND (s->>'status_message' LIKE '%max_tokens%' OR s->>'status_message' LIKE '%max_completion_tokens%')
            LIMIT 5
        """)
        )
        rows = r.fetchall()
        print(f"Found {len(rows)} samples:\n")
        for i, row in enumerate(rows, 1):
            # Try to extract model from attributes
            try:
                attrs = json.loads(row.attrs) if row.attrs else {}
                model = attrs.get("gen_ai.request.model", "unknown")
            except Exception:
                model = "parse_error"
            print(f"  [{i}] model={model}")
            print(f"      {row.msg}\n")

        # ── 3. null content errors — what messages are sent? ──
        print("=" * 80)
        print("3. NULL CONTENT ERRORS")
        print("=" * 80)
        r = await session.execute(
            text("""
            SELECT 
                s->>'attributes' as attrs,
                LEFT(s->>'status_message', 200) as msg
            FROM traces t, jsonb_array_elements(t.spans) s
            WHERE t.start_time >= '2026-03-05'
              AND s->>'status' = 'error'
              AND s->>'status_message' LIKE '%expected a string, got null%'
            LIMIT 5
        """)
        )
        rows = r.fetchall()
        print(f"Found {len(rows)} samples:\n")
        for i, row in enumerate(rows, 1):
            try:
                attrs = json.loads(row.attrs) if row.attrs else {}
                model = attrs.get("gen_ai.request.model", "unknown")
                prompt_name = attrs.get("prompt_template.system_name", "unknown")
            except Exception:
                model, prompt_name = "parse_error", "parse_error"
            print(f"  [{i}] model={model} prompt={prompt_name}")
            print(f"      {row.msg}\n")

        # ── 4. Connection pool errors ──
        print("=" * 80)
        print("4. CONNECTION POOL ERRORS")
        print("=" * 80)
        r = await session.execute(
            text("""
            SELECT 
                LEFT(s->>'status_message', 300) as msg,
                s->>'name' as span_name,
                t.name as trace_name
            FROM traces t, jsonb_array_elements(t.spans) s
            WHERE t.start_time >= '2026-03-05'
              AND s->>'status' = 'error'
              AND s->>'status_message' LIKE '%Connection pool%'
            LIMIT 5
        """)
        )
        rows = r.fetchall()
        print(f"Found {len(rows)} samples:\n")
        for i, row in enumerate(rows, 1):
            print(f"  [{i}] trace={row.trace_name} span={row.span_name}")
            print(f"      {row.msg[:200]}\n")

        # ── 5. Authentication errors — which providers? ──
        print("=" * 80)
        print("5. AUTHENTICATION ERRORS")
        print("=" * 80)
        r = await session.execute(
            text("""
            SELECT 
                s->>'attributes' as attrs,
                LEFT(s->>'status_message', 200) as msg
            FROM traces t, jsonb_array_elements(t.spans) s
            WHERE t.start_time >= '2026-03-05'
              AND s->>'status' = 'error'
              AND (s->>'status_message' LIKE '%AuthenticationError%' 
                   OR s->>'status_message' LIKE '%Missing credentials%')
            LIMIT 5
        """)
        )
        rows = r.fetchall()
        print(f"Found {len(rows)} samples:\n")
        for i, row in enumerate(rows, 1):
            try:
                attrs = json.loads(row.attrs) if row.attrs else {}
                model = attrs.get("gen_ai.request.model", "unknown")
            except Exception:
                model = "parse_error"
            print(f"  [{i}] model={model}")
            print(f"      {row.msg}\n")

        # ── 6. All other errors ──
        print("=" * 80)
        print("6. OTHER ERRORS")
        print("=" * 80)
        r = await session.execute(
            text("""
            SELECT 
                LEFT(s->>'status_message', 300) as msg,
                s->>'name' as span_name
            FROM traces t, jsonb_array_elements(t.spans) s
            WHERE t.start_time >= '2026-03-05'
              AND s->>'status' = 'error'
              AND s->>'status_message' NOT LIKE '%max_tokens%'
              AND s->>'status_message' NOT LIKE '%max_completion_tokens%'
              AND s->>'status_message' NOT LIKE '%Invalid schema for response_format%'
              AND s->>'status_message' NOT LIKE '%expected a string, got null%'
              AND s->>'status_message' NOT LIKE '%AuthenticationError%'
              AND s->>'status_message' NOT LIKE '%Missing credentials%'
              AND s->>'status_message' NOT LIKE '%Connection pool%'
              AND s->>'status_message' NOT LIKE '%LLM Provider NOT provided%'
            LIMIT 10
        """)
        )
        rows = r.fetchall()
        print(f"Found {len(rows)} other errors:\n")
        for i, row in enumerate(rows, 1):
            print(f"  [{i}] span={row.span_name}")
            print(f"      {row.msg[:250]}\n")

        # ── 7. Total today from our test run vs other ──
        print("=" * 80)
        print("7. TRACES BY SOURCE (today)")
        print("=" * 80)
        r = await session.execute(
            text("""
            SELECT source, count(*) as cnt
            FROM traces
            WHERE start_time >= '2026-03-05'
            GROUP BY source
            ORDER BY cnt DESC
        """)
        )
        rows = r.fetchall()
        for row in rows:
            print(f"  {row.source or 'NULL'}: {row.cnt}")


asyncio.run(main())
