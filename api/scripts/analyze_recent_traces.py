#!/usr/bin/env python3
"""Analyze traces from the LATEST test run only."""

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
        # Find the start of the last test run (latest batch of traces)
        r = await session.execute(
            text("""
            SELECT max(start_time) as latest FROM traces
        """)
        )
        latest = r.scalar()
        print(f"Latest trace: {latest}")

        # Get traces from the last 10 minutes
        r = await session.execute(
            text("""
            SELECT count(*) as total,
                   count(*) FILTER (WHERE status = 'success') as ok,
                   count(*) FILTER (WHERE status = 'error') as err,
                   count(*) FILTER (WHERE status IS NULL OR status NOT IN ('success','error')) as other,
                   min(start_time) as first_ts,
                   max(start_time) as last_ts
            FROM traces
            WHERE start_time >= now() - interval '15 minutes'
        """)
        )
        row = r.fetchone()
        print("\n=== RECENT TRACES (last 15 min) ===")
        print(
            f"Total: {row.total}, Success: {row.ok}, Error: {row.err}, Other: {row.other}"
        )
        print(f"Time range: {row.first_ts} → {row.last_ts}")

        # Mismatches in recent traces
        r = await session.execute(
            text("""
            SELECT count(*) FROM traces
            WHERE start_time >= now() - interval '15 minutes'
              AND status = 'success'
              AND EXISTS (SELECT 1 FROM jsonb_array_elements(spans) s WHERE s->>'status' = 'error')
        """)
        )
        recent_mismatches = r.scalar()
        print(f"Mismatches (status=success but has error spans): {recent_mismatches}")

        # Recent error categories
        r = await session.execute(
            text("""
            SELECT
              CASE
                WHEN s->>'status_message' LIKE '%max_tokens%' OR s->>'status_message' LIKE '%max_completion_tokens%' THEN 'max_tokens issue'
                WHEN s->>'status_message' LIKE '%Invalid schema for response_format%' THEN 'Invalid response_format schema'
                WHEN s->>'status_message' LIKE '%expected a string, got null%' THEN 'null content in messages'
                WHEN s->>'status_message' LIKE '%AuthenticationError%' OR s->>'status_message' LIKE '%401%' THEN 'AuthenticationError'
                WHEN s->>'status_message' LIKE '%LLM Provider NOT provided%' THEN 'LLM Provider not provided'
                WHEN s->>'status_message' LIKE '%Expecting%delimiter%' OR s->>'status_message' LIKE '%Expecting value%' THEN 'JSON parse error'
                WHEN s->>'status_message' LIKE '%NotFoundError%' OR s->>'status_message' LIKE '%404%' THEN 'NotFoundError'
                WHEN s->>'status_message' LIKE '%Connection pool%' THEN 'Connection pool'
                WHEN s->>'status_message' LIKE '%Missing credentials%' THEN 'Missing credentials'
                ELSE 'Other: ' || LEFT(s->>'status_message', 120)
              END as error_category,
              count(*) as cnt
            FROM traces t, jsonb_array_elements(t.spans) s
            WHERE t.start_time >= now() - interval '15 minutes'
              AND s->>'status' = 'error'
            GROUP BY error_category
            ORDER BY cnt DESC
        """)
        )
        rows = r.fetchall()
        total_err = sum(row.cnt for row in rows)
        print(f"\n=== ERROR CATEGORIES (recent, total: {total_err}) ===")
        for row in rows:
            print(f"  {row.cnt:4d}  {row.error_category}")

        # Show traces with error status (should now exist after our fix)
        r = await session.execute(
            text("""
            SELECT id, name, status, 
                   jsonb_array_length(spans) as span_count,
                   (SELECT count(*) FROM jsonb_array_elements(spans) s WHERE s->>'status' = 'error') as err_spans
            FROM traces
            WHERE start_time >= now() - interval '15 minutes'
              AND status = 'error'
            LIMIT 10
        """)
        )
        rows = r.fetchall()
        print("\n=== TRACES WITH status='error' (recent, first 10) ===")
        if rows:
            for row in rows:
                print(
                    f"  {row.status:8s} | spans={row.span_count} err_spans={row.err_spans} | {row.name}"
                )
        else:
            print("  (none found — trace status fix may not be working)")

        # Compare: show a few recent success traces that have error spans
        r = await session.execute(
            text("""
            SELECT id, name, status,
                   (SELECT count(*) FROM jsonb_array_elements(spans) s WHERE s->>'status' = 'error') as err_spans,
                   LEFT((SELECT s->>'status_message' FROM jsonb_array_elements(spans) s WHERE s->>'status' = 'error' LIMIT 1), 150) as first_err
            FROM traces
            WHERE start_time >= now() - interval '15 minutes'
              AND status = 'success'
              AND EXISTS (SELECT 1 FROM jsonb_array_elements(spans) s WHERE s->>'status' = 'error')
            LIMIT 10
        """)
        )
        rows = r.fetchall()
        print(
            "\n=== MISMATCHED TRACES (status=success but has error spans, first 10) ==="
        )
        if rows:
            for row in rows:
                print(f"  {row.status:8s} | err_spans={row.err_spans} | {row.name}")
                print(
                    f"           err: {row.first_err[:120] if row.first_err else 'N/A'}"
                )
        else:
            print("  (none — all traces with errors correctly have status='error'!)")


asyncio.run(main())
