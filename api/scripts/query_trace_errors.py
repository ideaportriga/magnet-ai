#!/usr/bin/env python3
"""Query traces table to find status mismatches and errors."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.config.app import alchemy
from sqlalchemy import text


async def main():
    async with alchemy.get_session() as session:
        result = await session.execute(
            text("""
            SELECT id, name, type, status, channel, source,
                   start_time, latency,
                   jsonb_array_length(spans) as span_count,
                   (SELECT count(*) FROM jsonb_array_elements(spans) s WHERE s->>'status' = 'error') as error_span_count
            FROM traces
            WHERE start_time >= '2026-03-05'
            ORDER BY start_time DESC
            LIMIT 30
        """)
        )
        rows = result.fetchall()
        print(f"Found {len(rows)} traces from today\n")
        mismatches = 0
        for r in rows:
            mismatch = r.status == "success" and r.error_span_count > 0
            if mismatch:
                mismatches += 1
            indicator = " <<< MISMATCH" if mismatch else ""
            print(
                f"  {r.status:8s} | spans={r.span_count} err_spans={r.error_span_count} | {str(r.name)[:50]:50s} | {r.latency or 0:.0f}ms{indicator}"
            )

        print(f"\nTotal mismatches (trace=success but has error spans): {mismatches}")

        # Show error details for mismatched traces
        if mismatches > 0:
            print("\n--- Error details for mismatched traces ---")
            result2 = await session.execute(
                text("""
                SELECT t.id, t.name, t.status,
                       s->>'name' as span_name,
                       s->>'status' as span_status,
                       s->>'status_message' as status_message
                FROM traces t,
                     jsonb_array_elements(t.spans) s
                WHERE t.start_time >= '2026-03-05'
                  AND t.status = 'success'
                  AND s->>'status' = 'error'
                ORDER BY t.start_time DESC
                LIMIT 20
            """)
            )
            err_rows = result2.fetchall()
            for er in err_rows:
                print(f"\n  Trace: {er.name} (id={er.id}, trace_status={er.status})")
                print(f"  Span:  {er.span_name} -> {er.span_status}")
                msg = str(er.status_message or "")[:200]
                print(f"  Error: {msg}")


asyncio.run(main())
