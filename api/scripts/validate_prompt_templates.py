#!/usr/bin/env python3
"""
Script to validate all prompt templates stored in the database.

Loads every prompt template, resolves its active variant, flattens the config,
and checks that:
  1. The template record can be read and parsed (schema validation).
  2. An active variant exists and can be resolved.
  3. The variant references a valid model (system_name_for_model → ai_models table).
  4. The referenced model has a provider_system_name configured.
  5. The system prompt text has no unresolved placeholders (optional — warn only).
  6. temperature / topP / maxTokens are within expected ranges.
  7. response_format, if present, is well-formed JSON Schema.

Usage:
    cd api
    python scripts/validate_prompt_templates.py          # pretty table
    python scripts/validate_prompt_templates.py --json    # machine-readable JSON
"""

from __future__ import annotations

import asyncio
import json
import re
import sys
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

# ---------- path bootstrap ----------
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.config.app import alchemy  # noqa: E402
from core.domain.prompts.schemas import Prompt, PromptVariantSchema  # noqa: E402
from core.domain.prompts.service import PromptsService  # noqa: E402
from core.domain.ai_models.service import AIModelsService  # noqa: E402
from core.domain.ai_models.schemas import AIModel  # noqa: E402
from prompt_templates.prompt_templates import transform_to_flat  # noqa: E402


# ────────────────────────────────── types ──────────────────────────────────


class Severity(StrEnum):
    ERROR = "error"
    WARNING = "warning"


@dataclass
class Issue:
    severity: Severity
    category: str
    message: str


@dataclass
class TemplateReport:
    system_name: str
    name: str
    variant: str | None = None
    issues: list[Issue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(i.severity == Severity.ERROR for i in self.issues)


# ─────────────────────────────── validators ───────────────────────────────

PLACEHOLDER_RE = re.compile(r"\{(\w+)\}")


def _validate_variant_schema(variant_dict: dict) -> list[Issue]:
    """Try to parse variant through Pydantic and report validation failures."""
    issues: list[Issue] = []
    try:
        PromptVariantSchema.model_validate(variant_dict)
    except Exception as exc:
        issues.append(
            Issue(
                Severity.ERROR,
                "schema_validation",
                f"Variant Pydantic validation failed: {exc}",
            )
        )
    return issues


def _validate_temperature(value: float | None) -> list[Issue]:
    if value is None:
        return []
    issues: list[Issue] = []
    if not (0.0 <= value <= 2.0):
        issues.append(
            Issue(
                Severity.ERROR,
                "parameter_range",
                f"temperature={value} is out of range [0, 2]",
            )
        )
    return issues


def _validate_top_p(value: float | None) -> list[Issue]:
    if value is None:
        return []
    issues: list[Issue] = []
    if not (0.0 <= value <= 1.0):
        issues.append(
            Issue(
                Severity.ERROR,
                "parameter_range",
                f"topP={value} is out of range [0, 1]",
            )
        )
    return issues


def _validate_max_tokens(value: int | None) -> list[Issue]:
    if value is None:
        return []
    issues: list[Issue] = []
    if value <= 0:
        issues.append(
            Issue(
                Severity.ERROR,
                "parameter_range",
                f"maxTokens={value} must be positive",
            )
        )
    return issues


def _validate_response_format(rf: dict | None) -> list[Issue]:
    """Check response_format is a reasonable OpenAI-compatible dict."""
    if rf is None:
        return []
    issues: list[Issue] = []
    if not isinstance(rf, dict):
        issues.append(
            Issue(
                Severity.ERROR,
                "response_format",
                f"response_format must be a dict, got {type(rf).__name__}",
            )
        )
        return issues
    # OpenAI expects {"type": "json_object"} or {"type": "json_schema", "json_schema": {...}}
    rf_type = rf.get("type")
    if rf_type not in (None, "json_object", "json_schema", "text"):
        issues.append(
            Issue(
                Severity.WARNING,
                "response_format",
                f"Unexpected response_format.type='{rf_type}'",
            )
        )
    if rf_type == "json_schema" and "json_schema" not in rf:
        issues.append(
            Issue(
                Severity.ERROR,
                "response_format",
                "response_format.type='json_schema' but 'json_schema' key is missing",
            )
        )
    return issues


def _validate_placeholders(text: str | None) -> list[Issue]:
    """Warn about placeholders that look unresolved (informational)."""
    if not text:
        return []
    matches = PLACEHOLDER_RE.findall(text)
    if matches:
        return [
            Issue(
                Severity.WARNING,
                "unresolved_placeholders",
                f"System prompt contains placeholders that require runtime values: {matches}",
            )
        ]
    return []


# ─────────────────────────────── main logic ───────────────────────────────


async def _load_all_models(session) -> dict[str, dict]:
    """Load all AI models into a lookup dict keyed by system_name."""
    service = AIModelsService(session=session)
    models, _ = await service.list_and_count()
    lookup: dict[str, dict] = {}
    for m in models:
        schema = service.to_schema(m, schema_type=AIModel)
        d = schema.model_dump()
        lookup[d["system_name"]] = d
    return lookup


async def validate_all() -> list[TemplateReport]:
    reports: list[TemplateReport] = []

    async with alchemy.get_session() as session:
        # Pre-load all models for cross-reference checks
        model_lookup = await _load_all_models(session)

        # Load all prompt templates
        service = PromptsService(session=session)
        prompts, total = await service.list_and_count()

        print(f"Found {total} prompt template(s) in the database.\n")

        for prompt_obj in prompts:
            # ── 1. Schema parsing ──
            try:
                prompt_schema = service.to_schema(prompt_obj, schema_type=Prompt)
                prompt_dict = prompt_schema.model_dump()
            except Exception as exc:
                report = TemplateReport(
                    system_name=getattr(prompt_obj, "system_name", "???"),
                    name=getattr(prompt_obj, "name", "???"),
                )
                report.issues.append(
                    Issue(
                        Severity.ERROR,
                        "schema_parsing",
                        f"Failed to parse prompt record: {exc}",
                    )
                )
                reports.append(report)
                continue

            system_name = prompt_dict.get("system_name", "???")
            name = prompt_dict.get("name", "???")
            variants = prompt_dict.get("variants") or []
            active_variant_name = prompt_dict.get("active_variant")

            # ── 2. Check variants exist ──
            if not variants:
                report = TemplateReport(system_name=system_name, name=name)
                report.issues.append(
                    Issue(
                        Severity.WARNING,
                        "missing_variants",
                        "Prompt template has no variants defined",
                    )
                )
                reports.append(report)
                continue

            # ── 3. Check active variant exists ──
            variant_names = [v.get("variant") for v in variants]
            if active_variant_name and active_variant_name not in variant_names:
                report = TemplateReport(
                    system_name=system_name,
                    name=name,
                    variant=active_variant_name,
                )
                report.issues.append(
                    Issue(
                        Severity.ERROR,
                        "missing_active_variant",
                        f"active_variant='{active_variant_name}' not found among variants: {variant_names}",
                    )
                )
                reports.append(report)
                # still continue to validate each variant below

            # ── 4. Validate every variant ──
            for variant_dict in variants:
                vname = variant_dict.get("variant", "???")
                report = TemplateReport(
                    system_name=system_name,
                    name=name,
                    variant=vname,
                )

                # 4a. Pydantic schema validation
                report.issues.extend(_validate_variant_schema(variant_dict))

                # 4b. Flatten and check model reference
                try:
                    flat = transform_to_flat(dict(prompt_dict), variant=vname)
                except Exception as exc:
                    report.issues.append(
                        Issue(
                            Severity.ERROR,
                            "flatten_error",
                            f"transform_to_flat failed: {exc}",
                        )
                    )
                    reports.append(report)
                    continue

                model_sn = flat.get("system_name_for_model")
                if not model_sn:
                    report.issues.append(
                        Issue(
                            Severity.ERROR,
                            "missing_model",
                            "Variant has no system_name_for_model configured",
                        )
                    )
                else:
                    # 4c. Check that model exists
                    model_cfg = model_lookup.get(model_sn)
                    if not model_cfg:
                        report.issues.append(
                            Issue(
                                Severity.ERROR,
                                "model_not_found",
                                f"Model '{model_sn}' not found in ai_models table",
                            )
                        )
                    else:
                        # 4d. Check provider configured
                        if not model_cfg.get("provider_system_name"):
                            report.issues.append(
                                Issue(
                                    Severity.ERROR,
                                    "missing_provider",
                                    f"Model '{model_sn}' has no provider_system_name",
                                )
                            )
                        # Check ai_model (LLM identifier) configured
                        if not model_cfg.get("ai_model"):
                            report.issues.append(
                                Issue(
                                    Severity.WARNING,
                                    "missing_llm",
                                    f"Model '{model_sn}' has no ai_model (LLM identifier)",
                                )
                            )

                # 4e. Parameter range checks
                report.issues.extend(_validate_temperature(flat.get("temperature")))
                report.issues.extend(_validate_top_p(flat.get("topP")))
                report.issues.extend(_validate_max_tokens(flat.get("maxTokens")))

                # 4f. response_format check
                report.issues.extend(
                    _validate_response_format(flat.get("response_format"))
                )

                # 4g. Placeholder check (informational)
                report.issues.extend(_validate_placeholders(flat.get("text")))

                reports.append(report)

    return reports


# ─────────────────────────────── output ───────────────────────────────────


def print_summary(reports: list[TemplateReport]) -> None:
    total_errors = sum(
        1 for r in reports for i in r.issues if i.severity == Severity.ERROR
    )
    total_warnings = sum(
        1 for r in reports for i in r.issues if i.severity == Severity.WARNING
    )
    clean = sum(1 for r in reports if not r.issues)

    print("=" * 90)
    print("PROMPT TEMPLATE VALIDATION REPORT")
    print("=" * 90)

    # Group by template system_name
    seen: dict[str, list[TemplateReport]] = {}
    for r in reports:
        seen.setdefault(r.system_name, []).append(r)

    for sn, group in seen.items():
        header_name = group[0].name
        print(f"\n── {header_name} ({sn})")
        for r in group:
            variant_label = r.variant or "(no variant)"
            if not r.issues:
                print(f"   ✅ [{variant_label}]  OK")
            else:
                for issue in r.issues:
                    icon = "❌" if issue.severity == Severity.ERROR else "⚠️"
                    print(
                        f"   {icon} [{variant_label}] [{issue.category}] {issue.message}"
                    )

    print("\n" + "=" * 90)
    print(
        f"TOTAL: {len(reports)} variant(s) checked | "
        f"✅ {clean} clean  |  ❌ {total_errors} error(s)  |  ⚠️  {total_warnings} warning(s)"
    )
    print("=" * 90)

    # Error type summary
    if total_errors or total_warnings:
        print("\nISSUE TYPE BREAKDOWN:")
        category_counts: dict[str, dict[str, int]] = {}
        for r in reports:
            for i in r.issues:
                key = i.category
                if key not in category_counts:
                    category_counts[key] = {"error": 0, "warning": 0}
                category_counts[key][i.severity.value] += 1

        for cat, counts in sorted(category_counts.items()):
            parts = []
            if counts["error"]:
                parts.append(f"{counts['error']} error(s)")
            if counts["warning"]:
                parts.append(f"{counts['warning']} warning(s)")
            print(f"  • {cat}: {', '.join(parts)}")


def print_json(reports: list[TemplateReport]) -> None:
    data = []
    for r in reports:
        data.append(
            {
                "system_name": r.system_name,
                "name": r.name,
                "variant": r.variant,
                "has_errors": r.has_errors,
                "issues": [
                    {
                        "severity": i.severity.value,
                        "category": i.category,
                        "message": i.message,
                    }
                    for i in r.issues
                ],
            }
        )
    print(json.dumps(data, indent=2, ensure_ascii=False))


# ─────────────────────────────── entrypoint ───────────────────────────────


async def main() -> int:
    reports = await validate_all()
    if "--json" in sys.argv:
        print_json(reports)
    else:
        print_summary(reports)

    # Exit code: 1 if any errors found
    return 1 if any(r.has_errors for r in reports) else 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
