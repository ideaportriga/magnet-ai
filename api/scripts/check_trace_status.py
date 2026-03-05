"""Check trace status distribution in recent traces."""

import sys

sys.path.insert(0, "src")

from sqlalchemy import create_engine, text
from core.config.app import settings

engine = create_engine(settings.db.sync_url)
with engine.connect() as conn:
    # Trace status distribution (last 15 minutes)
    result = conn.execute(
        text(
            "SELECT status, count(*) FROM traces "
            "WHERE created_at > now() - interval '15 minutes' "
            "GROUP BY status"
        )
    )
    print("=== Trace Status Distribution (last 15 min) ===")
    for r in result.fetchall():
        print(f"  {r[0]}: {r[1]}")

    # Mismatches: status=success but has error spans
    result2 = conn.execute(
        text(
            "SELECT count(*) FROM traces "
            "WHERE created_at > now() - interval '15 minutes' "
            "AND status = 'success' "
            "AND EXISTS ("
            "  SELECT 1 FROM jsonb_array_elements(spans) AS s "
            "  WHERE s->>'status' = 'error'"
            ")"
        )
    )
    mismatched = result2.scalar()
    print(f"\nMismatched (status=success but has error spans): {mismatched}")

    # Total traces with error spans
    result3 = conn.execute(
        text(
            "SELECT count(*) FROM traces "
            "WHERE created_at > now() - interval '15 minutes' "
            "AND EXISTS ("
            "  SELECT 1 FROM jsonb_array_elements(spans) AS s "
            "  WHERE s->>'status' = 'error'"
            ")"
        )
    )
    total_with_errors = result3.scalar()
    print(f"Total traces with error spans: {total_with_errors}")

    # Sample error traces
    result4 = conn.execute(
        text(
            "SELECT id, name, status, created_at FROM traces "
            "WHERE created_at > now() - interval '15 minutes' "
            "AND status = 'error' "
            "ORDER BY created_at DESC LIMIT 10"
        )
    )
    rows = result4.fetchall()
    print(f"\n=== Error Traces (showing {len(rows)}) ===")
    for r in rows:
        print(f"  id={r[0][:12]}... name={r[1]} status={r[2]}")
