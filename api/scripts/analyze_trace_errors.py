#!/usr/bin/env python3
"""Comprehensive analysis of trace errors from the database."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import logging

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

from core.config.app import alchemy  # noqa: E402
from sqlalchemy import text  # noqa: E402


async def main():
    async with alchemy.get_session() as session:
        # 1. Total traces today
        r = await session.execute(
            text("""
            SELECT count(*) as total,
                   count(*) FILTER (WHERE status = 'success') as success_count,
                   count(*) FILTER (WHERE status = 'error') as error_count,
                   count(*) FILTER (WHERE status IS NULL OR status NOT IN ('success','error')) as other_count
            FROM traces WHERE start_time >= '2026-03-05'
        """)
        )
        row = r.fetchone()
        print("=== Traces today ===")
        print(
            f"Total: {row.total}, Success: {row.success_count}, Error: {row.error_count}, Other: {row.other_count}"
        )

        # 2. Mismatches (trace=success but has error spans)
        r = await session.execute(
            text("""
            SELECT count(*) as cnt FROM traces
            WHERE start_time >= '2026-03-05' AND status = 'success'
              AND EXISTS (SELECT 1 FROM jsonb_array_elements(spans) s WHERE s->>'status' = 'error')
        """)
        )
        print(f"Mismatches (trace=success, has error spans): {r.scalar()}")

        # 3. Error categories from error spans
        r = await session.execute(
            text("""
            SELECT
              CASE
                WHEN s->>'status_message' LIKE '%max_tokens%' OR s->>'status_message' LIKE '%max_completion_tokens%' THEN 'max_tokens issue'
                WHEN s->>'status_message' LIKE '%Invalid schema for response_format%' THEN 'Invalid response_format schema'
                WHEN s->>'status_message' LIKE '%additionalProperties%' THEN 'additionalProperties in schema'
                WHEN s->>'status_message' LIKE '%expected a string, got null%' THEN 'null content in messages'
                WHEN s->>'status_message' LIKE '%AuthenticationError%' OR s->>'status_message' LIKE '%401%' THEN 'AuthenticationError'
                WHEN s->>'status_message' LIKE '%LLM Provider NOT provided%' THEN 'LLM Provider not provided'
                WHEN s->>'status_message' LIKE '%JSONDecodeError%' OR s->>'status_message' LIKE '%Expecting%delimiter%' OR s->>'status_message' LIKE '%Expecting value%' THEN 'JSON parse error'
                WHEN s->>'status_message' LIKE '%NotFoundError%' OR s->>'status_message' LIKE '%404%' THEN 'NotFoundError'
                ELSE 'Other: ' || LEFT(s->>'status_message', 100)
              END as error_category,
              count(*) as cnt
            FROM traces t, jsonb_array_elements(t.spans) s
            WHERE t.start_time >= '2026-03-05' AND s->>'status' = 'error'
            GROUP BY error_category
            ORDER BY cnt DESC
        """)
        )
        rows = r.fetchall()
        total_errors = sum(row.cnt for row in rows)
        print(f"\n=== Error categories (from error spans, total: {total_errors}) ===")
        for row in rows:
            print(f"  {row.cnt:4d}  {row.error_category}")

        # 4. Check specifically for max_tokens errors
        r = await session.execute(
            text("""
            SELECT count(*) FROM traces t, jsonb_array_elements(t.spans) s
            WHERE t.start_time >= '2026-03-05'
              AND (s->>'status_message' LIKE '%max_tokens%' OR s->>'status_message' LIKE '%max_completion_tokens%')
        """)
        )
        print(f"\nmax_tokens related errors today: {r.scalar()}")

        # 5. Error span details - unique error messages
        r = await session.execute(
            text("""
            SELECT DISTINCT LEFT(s->>'status_message', 200) as msg
            FROM traces t, jsonb_array_elements(t.spans) s
            WHERE t.start_time >= '2026-03-05' AND s->>'status' = 'error'
            LIMIT 30
        """)
        )
        rows = r.fetchall()
        print("\n=== Unique error messages (first 200 chars) ===")
        for i, row in enumerate(rows, 1):
            print(f"\n  [{i}] {row.msg}")

        # 6. Errors by hour
        r = await session.execute(
            text("""
            SELECT date_trunc('hour', t.start_time) as hour,
                   count(DISTINCT t.id) as traces_with_errors
            FROM traces t, jsonb_array_elements(t.spans) s
            WHERE t.start_time >= '2026-03-05' AND s->>'status' = 'error'
            GROUP BY hour ORDER BY hour
        """)
        )
        rows = r.fetchall()
        print("\n=== Error traces by hour ===")
        for row in rows:
            print(f"  {row.hour}  {row.traces_with_errors} traces with errors")


asyncio.run(main())
