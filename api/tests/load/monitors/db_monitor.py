"""Database monitoring sidecar for load tests.

Run alongside Locust to capture PostgreSQL metrics during load testing.
Outputs JSON Lines to reports/db_monitor.jsonl.

Usage:
    python -m tests.load.monitors.db_monitor \
        --dsn "postgresql://postgres:postgres@localhost:5433/magnet_dev" \
        --interval 1.0 \
        --output reports/db_monitor.jsonl
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import signal
import time

logger = logging.getLogger(__name__)

QUERIES = {
    "active_connections": (
        "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
    ),
    "idle_connections": ("SELECT count(*) FROM pg_stat_activity WHERE state = 'idle'"),
    "waiting_locks": ("SELECT count(*) FROM pg_locks WHERE NOT granted"),
    "deadlocks": (
        "SELECT deadlocks FROM pg_stat_database WHERE datname = current_database()"
    ),
    "long_queries_5s": (
        "SELECT count(*) FROM pg_stat_activity "
        "WHERE state = 'active' AND now() - query_start > interval '5 seconds'"
    ),
    "long_queries_1s": (
        "SELECT count(*) FROM pg_stat_activity "
        "WHERE state = 'active' AND now() - query_start > interval '1 second'"
    ),
    "total_connections": ("SELECT count(*) FROM pg_stat_activity"),
}

LOCK_DETAILS_QUERY = """
    SELECT
        blocked.pid AS blocked_pid,
        blocking.pid AS blocking_pid,
        blocked_activity.query AS blocked_query,
        blocking_activity.query AS blocking_query
    FROM pg_locks blocked
    JOIN pg_stat_activity blocked_activity ON blocked_activity.pid = blocked.pid
    JOIN pg_locks blocking
        ON blocking.locktype = blocked.locktype
        AND blocking.database IS NOT DISTINCT FROM blocked.database
        AND blocking.relation IS NOT DISTINCT FROM blocked.relation
        AND blocking.pid != blocked.pid
    JOIN pg_stat_activity blocking_activity ON blocking_activity.pid = blocking.pid
    WHERE NOT blocked.granted
    LIMIT 10
"""

_running = True


def _handle_signal(sig, frame):
    global _running
    _running = False


async def monitor(dsn: str, interval: float, output: str) -> None:
    """Continuously collect DB metrics and write to JSONL file."""
    try:
        import asyncpg
    except ImportError:
        logger.error("asyncpg is required: pip install asyncpg")
        return

    conn = await asyncpg.connect(dsn)
    logger.info("Connected to database, monitoring every %.1fs -> %s", interval, output)

    with open(output, "w") as f:  # noqa: ASYNC230
        while _running:
            metrics: dict = {"timestamp": time.time()}

            for name, query in QUERIES.items():
                try:
                    result = await conn.fetchval(query)
                    metrics[name] = result
                except Exception as e:
                    metrics[name] = f"error: {e}"

            # Lock details if any waiting locks
            if metrics.get("waiting_locks", 0) > 0:
                try:
                    rows = await conn.fetch(LOCK_DETAILS_QUERY)
                    metrics["lock_details"] = [dict(r) for r in rows]
                except Exception:
                    metrics["lock_details"] = []

            f.write(json.dumps(metrics, default=str) + "\n")
            f.flush()

            # Log warnings
            if metrics.get("deadlocks", 0) > 0:
                logger.warning("DEADLOCKS detected: %s", metrics["deadlocks"])
            if metrics.get("waiting_locks", 0) > 5:
                logger.warning(
                    "High lock contention: %s waiting", metrics["waiting_locks"]
                )
            if metrics.get("long_queries_5s", 0) > 0:
                logger.warning("Long queries (>5s): %s", metrics["long_queries_5s"])

            await asyncio.sleep(interval)

    await conn.close()
    logger.info("Monitoring stopped.")


def main():
    parser = argparse.ArgumentParser(description="DB monitor for load tests")
    parser.add_argument(
        "--dsn",
        default="postgresql://postgres:postgres@localhost:5433/magnet_dev",
        help="PostgreSQL connection string",
    )
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--output", default="reports/db_monitor.jsonl")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    asyncio.run(monitor(args.dsn, args.interval, args.output))


if __name__ == "__main__":
    main()
