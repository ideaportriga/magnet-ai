"""Aggregate test reports into a single summary.json.

Reads individual test suite reports and produces a unified summary
that can be consumed by AI coding agents.

Usage:
    python scripts/aggregate_reports.py
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPORTS_DIR = Path(os.environ.get("REPORTS_DIR", "reports"))


def _load_json(path: Path) -> dict | None:
    """Load a JSON file, returning None if it doesn't exist."""
    if not path.exists():
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _load_jsonl(path: Path) -> list[dict]:
    """Load a JSON Lines file."""
    if not path.exists():
        return []
    lines = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    lines.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return lines


def _extract_pytest_summary(report: dict | None) -> dict:
    """Extract key info from a pytest-json-report file."""
    if not report:
        return {"status": "SKIPPED", "total": 0, "passed": 0, "failed": 0}

    summary = report.get("summary", {})
    total = summary.get("total", 0)
    passed = summary.get("passed", 0)
    failed = summary.get("failed", 0)
    errors = summary.get("error", 0)
    duration = report.get("duration", 0)

    status = (
        "PASS"
        if (failed + errors) == 0 and total > 0
        else "FAIL"
        if total > 0
        else "SKIPPED"
    )

    result: dict = {
        "status": status,
        "total": total,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "duration_seconds": round(duration, 2),
    }

    # Extract failure details
    if failed > 0 or errors > 0:
        failures = []
        for test in report.get("tests", []):
            if test.get("outcome") in ("failed", "error"):
                call_info = test.get("call", {})
                failures.append(
                    {
                        "test": test.get("nodeid", "unknown"),
                        "outcome": test.get("outcome"),
                        "message": call_info.get("longrepr", "")[:500],
                        "duration": call_info.get("duration", 0),
                    }
                )
        result["failures"] = failures[:20]  # Limit to 20 failures

    return result


def _extract_coverage(report: dict | None) -> dict | None:
    """Extract coverage percentage from pytest-cov JSON report."""
    if not report:
        return None
    totals = report.get("totals", {})
    return {
        "percent_covered": totals.get("percent_covered", 0),
        "covered_lines": totals.get("covered_lines", 0),
        "num_statements": totals.get("num_statements", 0),
        "missing_lines": totals.get("missing_lines", 0),
    }


def _extract_load_summary(report: dict | None) -> dict:
    """Extract key metrics from Locust JSON output."""
    if not report:
        return {"status": "SKIPPED"}

    # Locust JSON output is a list of request stats
    if isinstance(report, list):
        total_requests = sum(r.get("num_requests", 0) for r in report)
        total_failures = sum(r.get("num_failures", 0) for r in report)
        avg_response = sum(
            r.get("avg_response_time", 0) * r.get("num_requests", 1) for r in report
        ) / max(total_requests, 1)
        p95_values = [
            r.get("response_times", {}).get("0.95", 0)
            for r in report
            if r.get("response_times")
        ]
        p95 = max(p95_values) if p95_values else 0
    else:
        total_requests = report.get("num_requests", 0)
        total_failures = report.get("num_failures", 0)
        avg_response = report.get("avg_response_time", 0)
        p95 = 0

    error_rate = (total_failures / max(total_requests, 1)) * 100

    status = (
        "PASS"
        if error_rate < 0.1 and p95 < 500
        else "WARN"
        if error_rate < 1
        else "FAIL"
    )

    return {
        "status": status,
        "total_requests": total_requests,
        "total_failures": total_failures,
        "error_rate_percent": round(error_rate, 3),
        "avg_response_ms": round(avg_response, 1),
        "p95_ms": round(p95, 1),
    }


def _extract_db_monitor_summary(metrics: list[dict]) -> dict | None:
    """Extract summary from DB monitor JSONL."""
    if not metrics:
        return None

    max_active = max((m.get("active_connections", 0) for m in metrics), default=0)
    max_waiting = max((m.get("waiting_locks", 0) for m in metrics), default=0)
    total_deadlocks = max((m.get("deadlocks", 0) for m in metrics), default=0)
    max_long_queries = max((m.get("long_queries_5s", 0) for m in metrics), default=0)

    warnings = []
    if total_deadlocks > 0:
        warnings.append(f"{total_deadlocks} deadlock(s) detected")
    if max_waiting > 5:
        warnings.append(f"Max {max_waiting} waiting locks")
    if max_long_queries > 0:
        warnings.append(f"Max {max_long_queries} queries >5s")

    return {
        "samples": len(metrics),
        "max_active_connections": max_active,
        "max_waiting_locks": max_waiting,
        "total_deadlocks": total_deadlocks,
        "max_long_queries_5s": max_long_queries,
        "warnings": warnings,
    }


def aggregate() -> dict:
    """Build the aggregated summary."""
    summary: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overall_status": "PASS",
        "suites": {},
    }

    # Test suites
    for suite_name in ("unit", "integration", "e2e", "fuzz"):
        report = _load_json(REPORTS_DIR / f"{suite_name}.json")
        suite_summary = _extract_pytest_summary(report)

        # Add coverage if available
        coverage_report = _load_json(REPORTS_DIR / f"coverage-{suite_name}.json")
        coverage = _extract_coverage(coverage_report)
        if coverage:
            suite_summary["coverage"] = coverage

        summary["suites"][suite_name] = suite_summary

        if suite_summary["status"] == "FAIL":
            summary["overall_status"] = "FAIL"

    # Load test
    for profile in ("smoke", "standard", "stress", "soak"):
        load_report = _load_json(REPORTS_DIR / f"load-{profile}.json")
        if load_report:
            load_summary = _extract_load_summary(load_report)
            summary["suites"][f"load_{profile}"] = load_summary
            if load_summary["status"] == "FAIL":
                summary["overall_status"] = "FAIL"

    # DB monitor
    db_metrics = _load_jsonl(REPORTS_DIR / "db_monitor.jsonl")
    db_summary = _extract_db_monitor_summary(db_metrics)
    if db_summary:
        summary["db_monitoring"] = db_summary
        if db_summary.get("total_deadlocks", 0) > 0:
            summary["overall_status"] = "FAIL"

    return summary


def main():
    os.makedirs(REPORTS_DIR, exist_ok=True)
    result = aggregate()

    output_path = REPORTS_DIR / "summary.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Summary written to {output_path}")
    print(f"Overall status: {result['overall_status']}")
    for name, suite in result.get("suites", {}).items():
        status = suite.get("status", "?")
        total = suite.get("total", suite.get("total_requests", "?"))
        print(f"  {name}: {status} ({total} tests/requests)")

    # Exit with non-zero if any suite failed
    if result["overall_status"] == "FAIL":
        sys.exit(1)


if __name__ == "__main__":
    main()
