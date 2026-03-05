#!/usr/bin/env python3
"""Check response_format schemas from prompt templates that caused errors."""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import logging

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

from core.config.app import alchemy  # noqa: E402
from sqlalchemy import text  # noqa: E402


# Templates that had response_format schema errors
ERROR_TEMPLATES = [
    "DEFAULT_DEEP_RESEARCH_ANALYZE_SEARCH_RESULTS",
    "LIAA_REASONING_PROMPT",
    "MF_AIRLINE_CASE_CLASSIFICATION",
    "NZ_PARTS_DEFAULT_DEEP_SEARCH_REASINING",
    "STT_TRANSCRIPT_POSTPROCESSING",
    "DEFAULT_DEEP_RESEARCH_REASONING",
    "JM_COMPANY_DEFAULT_DEEP_RESEARCH_REASONING",
    "NZ_PARTS_DEFAULT_DEEP_RESEARCH_ANALYZE_SEARCH_RESULTS",
]


async def main():
    async with alchemy.get_session() as session:
        for name in ERROR_TEMPLATES[:3]:  # check first 3
            r = await session.execute(
                text("""
                SELECT system_name, variants
                FROM prompts
                WHERE system_name = :name
            """),
                {"name": name},
            )
            row = r.fetchone()
            if not row:
                print(f"\n--- {name}: NOT FOUND ---")
                continue

            print(f"\n{'=' * 80}")
            print(f"TEMPLATE: {name}")
            print(f"{'=' * 80}")

            variants = (
                row.variants
                if isinstance(row.variants, list)
                else json.loads(row.variants)
            )
            for v in variants:
                if not v.get("isActive"):
                    continue
                rf = v.get("responseFormat")
                if rf:
                    print(f"\nVariant: {v.get('variantName', '?')}")
                    print(f"responseFormat type: {type(rf)}")
                    # Show the schema structure
                    if isinstance(rf, str):
                        rf = json.loads(rf)
                    print(json.dumps(rf, indent=2, ensure_ascii=False)[:1000])

                    # Check for missing additionalProperties and required
                    if isinstance(rf, dict):
                        schema = rf.get("json_schema", {}).get("schema", {})
                        if isinstance(schema, str):
                            schema = json.loads(schema)

                        def check_schema(s, path=""):
                            issues = []
                            if s.get("type") == "object":
                                if "additionalProperties" not in s:
                                    issues.append(
                                        f"{path}: missing 'additionalProperties: false'"
                                    )
                                props = s.get("properties", {})
                                required = set(s.get("required", []))
                                prop_keys = set(props.keys())
                                if props and required != prop_keys:
                                    missing = prop_keys - required
                                    extra = required - prop_keys
                                    if missing:
                                        issues.append(
                                            f"{path}: 'required' missing keys: {missing}"
                                        )
                                    if extra:
                                        issues.append(
                                            f"{path}: 'required' has extra keys: {extra}"
                                        )
                                for pname, pschema in props.items():
                                    issues.extend(
                                        check_schema(pschema, f"{path}.{pname}")
                                    )
                            if s.get("type") == "array" and "items" in s:
                                issues.extend(check_schema(s["items"], f"{path}[]"))
                            return issues

                        issues = check_schema(schema)
                        if issues:
                            print("\n  ⚠️  Schema issues found:")
                            for issue in issues:
                                print(f"    - {issue}")
                        else:
                            print("\n  ✅ Schema looks compliant")
                else:
                    print(f"\nVariant: {v.get('variantName', '?')} — no responseFormat")


asyncio.run(main())
