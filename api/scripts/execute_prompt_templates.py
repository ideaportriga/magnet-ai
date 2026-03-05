#!/usr/bin/env python3
"""
Script that actually EXECUTES every prompt template against the LLM
with mock data and reports successes / failures.

For each prompt template + variant:
  1. Loads the template from DB & flattens it.
  2. Extracts placeholders ({key}) from the system prompt text.
  3. Fills them with configurable mock values.
  4. Calls execute_prompt_template (real LLM call).
  5. Collects the result or the error.

Usage:
    cd api && source .venv/bin/activate

    # Execute ALL templates (active variant only):
    python scripts/execute_prompt_templates.py

    # Execute ALL variants of ALL templates:
    python scripts/execute_prompt_templates.py --all-variants

    # Execute only specific templates by system_name:
    python scripts/execute_prompt_templates.py --only template-a template-b

    # Dry-run: show what WOULD be executed without calling the LLM:
    python scripts/execute_prompt_templates.py --dry-run

    # Use a custom mock user message:
    python scripts/execute_prompt_templates.py --user-message "Tell me a joke"

    # Provide custom mock values for placeholders (JSON):
    python scripts/execute_prompt_templates.py --mock-values '{"language": "English", "topic": "AI"}'

    # Output as JSON:
    python scripts/execute_prompt_templates.py --json

    # Override max_tokens for all calls (to save cost):
    python scripts/execute_prompt_templates.py --max-tokens 50
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import re
import sys
import traceback
from dataclasses import dataclass, field
from pathlib import Path

# ── redirect all logging to stderr so stdout stays clean for --json ──
logging.basicConfig(stream=sys.stderr, level=logging.WARNING)
# Silence noisy SQLAlchemy / litellm loggers that default to stdout
for _logger_name in ("sqlalchemy", "sqlalchemy.engine", "litellm", "httpx", "openai"):
    logging.getLogger(_logger_name).handlers = []
    logging.getLogger(_logger_name).propagate = True

# ── path bootstrap ──
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.config.app import alchemy  # noqa: E402
from core.domain.prompts.schemas import Prompt  # noqa: E402
from core.domain.prompts.service import PromptsService  # noqa: E402
from prompt_templates.prompt_templates import transform_to_flat  # noqa: E402
from services.prompt_templates.services import execute_prompt_template  # noqa: E402

# ────────────────────────────────── types ──────────────────────────────────

PLACEHOLDER_RE = re.compile(r"\{(\w+)\}")

DEFAULT_MOCK_USER_MESSAGE = "This is an automated test. Reply with OK."

# Default mock values for common placeholders found in system prompts.
# Keys are lowercase; matching is case-insensitive.
DEFAULT_MOCK_VALUES: dict[str, str] = {
    "language": "English",
    "topic": "artificial intelligence",
    "context": "This is a test context for validation purposes.",
    "query": "What is 2+2?",
    "question": "What is 2+2?",
    "input": "sample input",
    "output": "sample output",
    "text": "sample text",
    "name": "Test User",
    "user_name": "Test User",
    "username": "Test User",
    "data": '{"key": "value"}',
    "json": '{"key": "value"}',
    "format": "plain text",
    "instructions": "Please respond briefly.",
    "history": "User: Hi\nAssistant: Hello!",
    "chat_history": "User: Hi\nAssistant: Hello!",
    "documents": "Document 1: Sample document content.",
    "sources": "Source 1: Sample source content.",
    "search_results": "Result 1: Sample search result.",
    "system": "You are a helpful assistant.",
    "persona": "a helpful assistant",
    "role": "assistant",
    "task": "answer the question",
    "goal": "provide a helpful response",
    "examples": "Example 1: Input -> Output",
    "schema": '{"type": "object"}',
    "tools": "[]",
    "date": "2026-03-05",
    "time": "12:00",
    "datetime": "2026-03-05T12:00:00Z",
    "count": "3",
    "limit": "10",
    "max": "100",
    "min": "1",
}


@dataclass
class ExecutionResult:
    system_name: str
    name: str
    variant: str
    status: str  # "success" | "error" | "skipped"
    content: str | None = None
    error_type: str | None = None
    error_message: str | None = None
    error_traceback: str | None = None
    latency_ms: float | None = None
    tokens: dict | None = None
    cost: float | None = None
    placeholders_found: list[str] = field(default_factory=list)
    mock_values_used: dict[str, str] = field(default_factory=dict)


# ────────────────────────────── helpers ────────────────────────────────


def _extract_placeholders(text: str | None) -> list[str]:
    """Extract {placeholder} names from system prompt text."""
    if not text:
        return []
    return PLACEHOLDER_RE.findall(text)


def _build_mock_values(
    placeholders: list[str],
    user_overrides: dict[str, str] | None = None,
) -> dict[str, str]:
    """Build mock values dict for the given placeholder names."""
    values: dict[str, str] = {}
    overrides = user_overrides or {}
    for p in placeholders:
        if p in overrides:
            values[p] = overrides[p]
        elif p.lower() in DEFAULT_MOCK_VALUES:
            values[p] = DEFAULT_MOCK_VALUES[p.lower()]
        else:
            values[p] = f"[mock:{p}]"
    return values


# ──────────────────────────── main execution ──────────────────────────


async def run_all(
    *,
    all_variants: bool = False,
    only: list[str] | None = None,
    limit: int = 0,
    dry_run: bool = False,
    user_message: str = DEFAULT_MOCK_USER_MESSAGE,
    mock_values_override: dict[str, str] | None = None,
    max_tokens_override: int | None = None,
) -> list[ExecutionResult]:
    results: list[ExecutionResult] = []

    async with alchemy.get_session() as session:
        service = PromptsService(session=session)
        prompts, total = await service.list_and_count()

        print(f"Found {total} prompt template(s) in the database.\n", file=sys.stderr)

        templates_processed = 0
        for prompt_obj in prompts:
            # Apply limit
            if limit > 0 and templates_processed >= limit:
                break
            try:
                prompt_schema = service.to_schema(prompt_obj, schema_type=Prompt)
                prompt_dict = prompt_schema.model_dump()
            except Exception as exc:
                results.append(
                    ExecutionResult(
                        system_name=getattr(prompt_obj, "system_name", "???"),
                        name=getattr(prompt_obj, "name", "???"),
                        variant="???",
                        status="error",
                        error_type=type(exc).__name__,
                        error_message=f"Failed to parse prompt from DB: {exc}",
                        error_traceback=traceback.format_exc(),
                    )
                )
                continue

            system_name = prompt_dict.get("system_name", "???")
            name = prompt_dict.get("name", "???")
            variants_list = prompt_dict.get("variants") or []
            active_variant = prompt_dict.get("active_variant")

            # Filter by --only
            if only and system_name not in only:
                continue

            templates_processed += 1

            if not variants_list:
                results.append(
                    ExecutionResult(
                        system_name=system_name,
                        name=name,
                        variant="(none)",
                        status="skipped",
                        error_message="No variants defined",
                    )
                )
                continue

            # Determine which variants to test
            if all_variants:
                variants_to_test = [v.get("variant") for v in variants_list]
            else:
                # Only the active variant (or first if no active)
                if active_variant:
                    variants_to_test = [active_variant]
                else:
                    variants_to_test = [variants_list[0].get("variant")]

            for vname in variants_to_test:
                # Flatten
                try:
                    flat = transform_to_flat(dict(prompt_dict), variant=vname)
                except Exception as exc:
                    results.append(
                        ExecutionResult(
                            system_name=system_name,
                            name=name,
                            variant=vname or "???",
                            status="error",
                            error_type=type(exc).__name__,
                            error_message=f"transform_to_flat failed: {exc}",
                            error_traceback=traceback.format_exc(),
                        )
                    )
                    continue

                # Extract placeholders and build mock values
                system_text = flat.get("text", "")
                placeholders = _extract_placeholders(system_text)
                mock_vals = _build_mock_values(placeholders, mock_values_override)

                model_sn = flat.get("system_name_for_model", "???")

                result = ExecutionResult(
                    system_name=system_name,
                    name=name,
                    variant=vname or "???",
                    placeholders_found=placeholders,
                    mock_values_used=mock_vals,
                    status="skipped" if dry_run else "pending",
                )

                if dry_run:
                    result.status = "skipped"
                    result.error_message = (
                        f"Dry-run — would call model='{model_sn}' "
                        f"with {len(placeholders)} placeholder(s): {placeholders}"
                    )
                    results.append(result)
                    _print_progress(result)
                    continue

                # ── Actually execute ──
                try:
                    # Build the config dict (already flat) and optionally override max_tokens
                    exec_config = dict(flat)
                    if max_tokens_override is not None:
                        exec_config["maxTokens"] = max_tokens_override

                    response = await execute_prompt_template(
                        system_name_or_config=exec_config,
                        template_values=mock_vals if mock_vals else None,
                        template_additional_messages=[
                            {"role": "user", "content": user_message},
                        ],
                    )

                    result.status = "success"
                    result.content = (
                        response.content[:200] + "…"
                        if response.content and len(response.content) > 200
                        else response.content
                    )
                    result.latency_ms = response.latency
                    result.tokens = response.usage
                    result.cost = response.cost

                except Exception as exc:
                    result.status = "error"
                    result.error_type = type(exc).__name__
                    result.error_message = str(exc)
                    result.error_traceback = traceback.format_exc()

                results.append(result)
                _print_progress(result)

    return results


def _print_progress(r: ExecutionResult) -> None:
    """Print a single-line progress indicator to stderr."""
    if r.status == "success":
        icon = "✅"
        detail = (
            f"latency={r.latency_ms:.0f}ms, tokens={r.tokens}" if r.latency_ms else ""
        )
    elif r.status == "skipped":
        icon = "⏭️"
        detail = r.error_message or ""
    else:
        icon = "❌"
        detail = f"{r.error_type}: {r.error_message}"

    print(f"  {icon} {r.system_name} [{r.variant}] — {detail}", file=sys.stderr)


# ────────────────────────────── reporting ──────────────────────────────


def print_summary(results: list[ExecutionResult]) -> None:
    successes = [r for r in results if r.status == "success"]
    errors = [r for r in results if r.status == "error"]
    skipped = [r for r in results if r.status == "skipped"]

    print("\n" + "=" * 90)
    print("PROMPT TEMPLATE EXECUTION REPORT")
    print("=" * 90)

    print(
        f"\nTOTAL: {len(results)} call(s)  |  "
        f"✅ {len(successes)} success  |  "
        f"❌ {len(errors)} error(s)  |  "
        f"⏭️  {len(skipped)} skipped"
    )

    if errors:
        print("\n── ERRORS ──")
        # Group by error type
        error_types: dict[str, list[ExecutionResult]] = {}
        for r in errors:
            et = r.error_type or "Unknown"
            error_types.setdefault(et, []).append(r)

        for et, group in sorted(error_types.items()):
            print(f"\n  🔴 {et} ({len(group)} occurrence(s)):")
            for r in group:
                print(f"     • {r.system_name} [{r.variant}]")
                print(f"       {r.error_message}")
                if r.error_traceback:
                    # Print last 3 lines of traceback for context
                    tb_lines = r.error_traceback.strip().split("\n")
                    for line in tb_lines[-3:]:
                        print(f"       {line}")

        print("\n── ERROR TYPE SUMMARY ──")
        for et, group in sorted(error_types.items()):
            print(f"  • {et}: {len(group)} occurrence(s)")

    if successes:
        total_tokens = sum((r.tokens or {}).get("total_tokens", 0) for r in successes)
        total_cost = sum(r.cost or 0 for r in successes)
        avg_latency = sum(r.latency_ms or 0 for r in successes) / len(successes)
        print("\n── SUCCESS STATS ──")
        print(f"  Total tokens used: {total_tokens}")
        print(f"  Total cost:        ${total_cost:.6f}")
        print(f"  Avg latency:       {avg_latency:.0f} ms")

    print("=" * 90)


def print_json(results: list[ExecutionResult]) -> None:
    data = []
    for r in results:
        entry = {
            "system_name": r.system_name,
            "name": r.name,
            "variant": r.variant,
            "status": r.status,
            "placeholders_found": r.placeholders_found,
            "mock_values_used": r.mock_values_used,
        }
        if r.status == "success":
            entry["content_preview"] = r.content
            entry["latency_ms"] = r.latency_ms
            entry["tokens"] = r.tokens
            entry["cost"] = r.cost
        elif r.status == "error":
            entry["error_type"] = r.error_type
            entry["error_message"] = r.error_message
            entry["error_traceback"] = r.error_traceback
        elif r.status == "skipped":
            entry["skip_reason"] = r.error_message
        data.append(entry)
    print(json.dumps(data, indent=2, ensure_ascii=False))


# ──────────────────────────── CLI ────────────────────────────


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Execute all prompt templates with mock data and report errors."
    )
    parser.add_argument(
        "--all-variants",
        action="store_true",
        help="Test every variant, not just the active one.",
    )
    parser.add_argument(
        "--only",
        nargs="+",
        metavar="SYSTEM_NAME",
        help="Only test these template system_names.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit the number of templates to test (0 = no limit).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be executed without calling the LLM.",
    )
    parser.add_argument(
        "--user-message",
        default=DEFAULT_MOCK_USER_MESSAGE,
        help=f"Mock user message (default: '{DEFAULT_MOCK_USER_MESSAGE}').",
    )
    parser.add_argument(
        "--mock-values",
        type=str,
        default=None,
        help='JSON dict of custom mock values for placeholders, e.g. \'{"language":"French"}\'.',
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=50,
        help="Override max_tokens for all calls to save cost (default: 50). Use 0 to keep original.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON instead of human-readable table.",
    )
    return parser.parse_args()


async def main() -> int:
    args = parse_args()

    mock_values_override = None
    if args.mock_values:
        try:
            mock_values_override = json.loads(args.mock_values)
        except json.JSONDecodeError as exc:
            print(f"❌ Invalid --mock-values JSON: {exc}", file=sys.stderr)
            return 2

    max_tokens = args.max_tokens if args.max_tokens and args.max_tokens > 0 else None

    print("🚀 Starting prompt template execution test...\n", file=sys.stderr)

    results = await run_all(
        all_variants=args.all_variants,
        only=args.only,
        limit=args.limit,
        dry_run=args.dry_run,
        user_message=args.user_message,
        mock_values_override=mock_values_override,
        max_tokens_override=max_tokens,
    )

    if args.json:
        print_json(results)
    else:
        print_summary(results)

    has_errors = any(r.status == "error" for r in results)

    # Force flush OTel span exporter before exit
    try:
        from services.observability.otel.config import otel_tracer_provider

        print("⏳ Flushing OTel exporter...", file=sys.stderr)
        otel_tracer_provider.force_flush(timeout_millis=10000)
        print("✅ OTel exporter flushed", file=sys.stderr)
    except Exception as e:
        print(f"⚠️ OTel flush failed: {e}", file=sys.stderr)

    return 1 if has_errors else 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
