#!/usr/bin/env python3
"""Debug trace status mismatch: check span count and timing."""

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
        # Get mismatched traces from last 15 min with full details
        r = await session.execute(
            text("""
            SELECT t.id, t.name, t.status,
                   jsonb_array_length(t.spans) as span_count,
                   t.start_time, t.end_time
            FROM traces t
            WHERE t.start_time >= now() - interval '15 minutes'
              AND t.status = 'success'
              AND EXISTS (SELECT 1 FROM jsonb_array_elements(t.spans) s WHERE s->>'status' = 'error')
            LIMIT 5
        """)
        )
        rows = r.fetchall()

        print(f"=== MISMATCHED TRACES (last 15 min): {len(rows)} found ===\n")
        for row in rows:
            print(f"Trace {row.id}: status={row.status}, spans={row.span_count}")
            print(f"  time: {row.start_time} → {row.end_time}")

            # Get individual spans in this trace
            r2 = await session.execute(
                text("""
                SELECT s->>'id' as span_id,
                       s->>'name' as span_name,
                       s->>'status' as span_status,
                       s->>'type' as span_type,
                       s->>'start_time' as start_time,
                       s->>'end_time' as end_time,
                       LEFT(s->>'status_message', 100) as msg
                FROM traces t, jsonb_array_elements(t.spans) s
                WHERE t.id = :tid
                ORDER BY s->>'start_time'
            """),
                {"tid": row.id},
            )
            spans = r2.fetchall()
            for sp in spans:
                err = f" — {sp.msg}" if sp.msg else ""
                print(
                    f"  span: {sp.span_name} [{sp.span_type}] status={sp.span_status}{err}"
                )
            print()


asyncio.run(main())
