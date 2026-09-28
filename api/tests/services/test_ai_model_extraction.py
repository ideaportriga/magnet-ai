"""Model settings extraction from pasted text (issue #466).

Covers the pure normalisation (matching targets, price cleanup, pricing-option
dedupe, per-source attribution) and the prompt-template call loop (fenced JSON, one validation retry,
json_schema rejection fallback, actionable errors).
"""

from __future__ import annotations

import json

import pytest

# Warm the import graph before the module under test is touched (same
# pre-existing circular-import chain as the other service unit tests).
import core.config.app  # noqa: F401

from services.ai_model_extraction import service as svc
from services.ai_model_extraction.schemas import (
    ExtractFromTextRequest,
    ExtractionOutput,
    ExtractionSource,
    ExtractionTarget,
)
from services.prompt_templates.models import PromptTemplateExecutionResponse


TARGETS = [
    ExtractionTarget(key="a", ai_model="gpt-4.1", type="prompts"),
    ExtractionTarget(key="b", ai_model="gpt-4.1-mini", type="prompts"),
]


def _output(*results: dict) -> ExtractionOutput:
    return ExtractionOutput.model_validate({"results": list(results)})


class TestNormalizeResults:
    def test_one_entry_per_target_in_request_order(self):
        out = svc.normalize_results(
            TARGETS,
            _output(
                {"target_key": "b", "matched_name": "GPT-4.1 mini"},
                {"target_key": "a", "matched_name": "GPT-4.1"},
            ),
        )
        assert [r.target_key for r in out] == ["a", "b"]

    def test_missing_and_unknown_targets(self):
        out = svc.normalize_results(
            TARGETS,
            _output(
                {"target_key": "zzz", "matched_name": "Other"},
                {"target_key": "a", "matched_name": "GPT-4.1"},
                {"target_key": "a", "matched_name": "Duplicate"},
            ),
        )
        assert out[0].matched_name == "GPT-4.1"
        assert out[1].target_key == "b"
        assert out[1].matched_name is None

    def test_not_found_drops_guessed_values(self):
        out = svc.normalize_results(
            TARGETS,
            _output(
                {
                    "target_key": "a",
                    "matched_name": "  ",
                    "description": "guess",
                    "tool_calling": True,
                    "pricing_options": [{"label": "Std", "price_input": "1"}],
                }
            ),
        )
        assert out[0].description is None
        assert out[0].tool_calling is None
        assert out[0].pricing_options == []

    def test_prices_are_cleaned(self):
        out = svc.normalize_results(
            TARGETS,
            _output(
                {
                    "target_key": "a",
                    "matched_name": "GPT-4.1",
                    "pricing_options": [
                        {
                            "label": "Global",
                            "price_input": "$2.00",
                            "price_output": 8,
                            "price_cached": "n/a",
                            "price_cache_write": "-1",
                            "price_long_context_input": "1,000",
                            "price_standard_input_unit_count": 0,
                            "price_scheme": "OpenAI",
                            "price_input_unit_name": "Tokens",
                            "price_output_unit_name": "words",
                        }
                    ],
                }
            ),
        )
        option = out[0].pricing_options[0]
        assert option.price_input == "2"
        assert option.price_output == "8"
        assert option.price_cached is None
        assert option.price_cache_write is None
        assert option.price_long_context_input == "1000"
        assert option.price_standard_input_unit_count is None
        assert option.price_scheme == "openai"
        assert option.price_input_unit_name == "tokens"
        assert option.price_output_unit_name is None

    def test_pricing_options_dedupe_and_drop_empty(self):
        out = svc.normalize_results(
            TARGETS,
            _output(
                {
                    "target_key": "a",
                    "matched_name": "GPT-4.1",
                    "pricing_options": [
                        {"label": "Standard", "price_input": "2"},
                        {"label": "standard", "price_input": "3"},
                        {"label": "No prices"},
                        {"label": "", "price_input": "1"},
                        {"label": "Batch", "price_input": "1", "price_output": "4"},
                    ],
                }
            ),
        )
        labels = [o.label for o in out[0].pricing_options]
        assert labels == ["Standard", "Option 4", "Batch"]
        assert out[0].pricing_options[0].price_input == "2"

    def test_description_and_features(self):
        out = svc.normalize_results(
            TARGETS,
            _output(
                {
                    "target_key": "a",
                    "matched_name": "GPT-4.1",
                    "description": "  Flagship model.  ",
                    "reasoning_effort_options": [" low", "low", "high"],
                    "vector_size": -5,
                }
            ),
        )
        assert out[0].description == "Flagship model."
        assert out[0].reasoning_effort_options == ["low", "high"]
        assert out[0].vector_size is None


def _priced(label: str, **prices) -> dict:
    return {"label": label, **prices}


def _options(*options: dict, source_count: int = 1):
    return svc.normalize_results(
        TARGETS,
        _output(
            {
                "target_key": "a",
                "matched_name": "GPT-4.1",
                "pricing_options": list(options),
            }
        ),
        source_count,
    )[0].pricing_options


class TestLongContext:
    def test_tiers_on_one_option_turn_long_context_on(self):
        (option,) = _options(
            _priced(
                "Standard",
                price_input="3",
                price_output="15",
                price_long_context_input="6",
                price_long_context_output="22.5",
            )
        )
        assert option.price_long_context_threshold == 200_000
        assert option.price_long_context_input == "6"

    def test_threshold_without_long_prices_is_dropped(self):
        (option,) = _options(
            _priced("Standard", price_input="3", price_long_context_threshold=128000)
        )
        assert option.price_long_context_threshold is None

    def test_tier_listed_as_its_own_option_is_merged(self):
        options = _options(
            _priced("Standard (<= 200K tokens)", price_input="3", price_output="15"),
            _priced("Standard (> 200K tokens)", price_input="6", price_output="22.5"),
            _priced("Batch", price_input="1.5", price_output="7.5"),
        )
        assert [o.label for o in options] == ["Standard", "Batch"]
        standard = options[0]
        assert standard.price_input == "3"
        assert standard.price_long_context_input == "6"
        assert standard.price_long_context_output == "22.5"
        assert standard.price_long_context_threshold == 200_000
        assert options[1].price_long_context_threshold is None

    def test_long_only_option_attaches_to_the_single_host(self):
        options = _options(
            _priced("Global", price_input="1.25", price_output="10"),
            _priced(
                "Long context",
                price_long_context_input="2.5",
                price_long_context_output="15",
                price_long_context_threshold=128000,
            ),
        )
        assert [o.label for o in options] == ["Global"]
        assert options[0].price_long_context_input == "2.5"
        assert options[0].price_long_context_threshold == 128000

    def test_threshold_is_read_from_the_tier_label(self):
        (option,) = _options(
            _priced("Standard", price_input="1"),
            _priced("Prompts over 128k tokens", price_input="2"),
        )
        assert option.price_long_context_threshold == 128_000

    def test_unrelated_options_stay_separate(self):
        options = _options(
            _priced("Global", price_input="2"),
            _priced("Data Zone", price_input="2.2"),
            _priced("> 200K", price_input="4"),
        )
        # Two possible hosts and no label match — keep the prices, don't guess.
        assert [o.label for o in options] == ["Global", "Data Zone", "> 200K"]


class TestSources:
    def test_source_is_kept_or_dropped_when_out_of_range(self):
        options = _options(
            _priced("Global", price_input="2", source=2),
            _priced("Batch", price_input="1", source=5),
            _priced("Priority", price_input="4", source=0),
            source_count=2,
        )
        assert [o.source for o in options] == [2, None, None]

    def test_same_label_from_two_sources_survives(self):
        options = _options(
            _priced("Standard", price_input="2", source=1),
            _priced("Standard", price_input="2.2", source=2),
            _priced("standard", price_input="9", source=2),
            source_count=2,
        )
        assert [(o.label, o.source, o.price_input) for o in options] == [
            ("Standard", 1, "2"),
            ("Standard", 2, "2.2"),
        ]

    def test_tier_never_merges_into_another_source(self):
        options = _options(
            _priced("Standard", price_input="3", source=1),
            _priced("Standard", price_input="2.5", source=2),
            _priced("Standard (> 200K tokens)", price_input="6", source=2),
            source_count=2,
        )
        assert [(o.source, o.price_long_context_input) for o in options] == [
            (1, None),
            (2, "6"),
        ]


def _source(text: str, **meta) -> ExtractionSource:
    return ExtractionSource(text=text, **meta)


class TestRequest:
    def test_blank_sources_are_dropped(self):
        request = ExtractFromTextRequest(
            sources=[_source(" docs "), _source("  ")], targets=TARGETS
        )
        assert [s.text for s in request.sources] == ["docs"]

    def test_needs_a_source(self):
        with pytest.raises(ValueError):
            ExtractFromTextRequest(sources=[_source("  ")], targets=TARGETS)

    def test_total_length_is_capped(self):
        with pytest.raises(ValueError):
            ExtractFromTextRequest(
                sources=[_source("x" * 60_000), _source("y" * 60_000)],
                targets=TARGETS,
            )

    def test_blank_meta_and_notes_are_dropped(self):
        request = ExtractFromTextRequest(
            sources=[_source("docs", site=" ", title="  Pricing ")],
            notes=["  use EU prices ", " "],
            targets=TARGETS,
        )
        assert request.sources[0].site is None
        assert request.sources[0].title == "Pricing"
        assert request.notes == ["use EU prices"]

    def test_long_note_is_rejected(self):
        with pytest.raises(ValueError):
            ExtractFromTextRequest(
                sources=[_source("docs")], notes=["x" * 1_001], targets=TARGETS
            )

    def test_user_message_numbers_sources_and_appends_notes(self):
        assert svc.build_user_message([_source("only")]) == "### Source 1\nonly"
        message = svc.build_user_message(
            [
                _source("model card"),
                _source("pricing", site="azure.microsoft.com", title="Azure pricing"),
            ],
            ["use Data Zone prices"],
        )
        assert message == (
            "### Source 1\nmodel card\n\n"
            '### Source 2 — azure.microsoft.com — "Azure pricing"\npricing\n\n'
            "### Notes from the admin\n- use Data Zone prices"
        )


class TestParseLlmJson:
    def test_fenced(self):
        assert svc.parse_llm_json('```json\n{"results": []}\n```') == {"results": []}

    @pytest.mark.parametrize("content", [None, "", "None", "[]", "not json"])
    def test_rejects(self, content):
        with pytest.raises(json.JSONDecodeError):
            svc.parse_llm_json(content)


def _request() -> ExtractFromTextRequest:
    return ExtractFromTextRequest(
        sources=[_source("pricing page")], provider="Azure", targets=TARGETS
    )


def _template(**overrides) -> dict:
    return {
        "system_name": svc.MODEL_EXTRACTION_PROMPT_TEMPLATE,
        "text": "{targets}",
        "system_name_for_model": "GPT",
        **overrides,
    }


def _patch_template(monkeypatch, config: dict | Exception) -> None:
    async def _fake(system_name, variant=None):
        if isinstance(config, Exception):
            raise config
        return dict(config)

    monkeypatch.setattr(
        "prompt_templates.prompt_templates.get_prompt_template_by_system_name_flat",
        _fake,
    )


def _patch_execute(monkeypatch, replies: list) -> list[dict]:
    calls: list[dict] = []

    async def _fake(**kwargs):
        calls.append(kwargs)
        reply = replies[len(calls) - 1]
        if isinstance(reply, Exception):
            raise reply
        return PromptTemplateExecutionResponse(content=reply)

    monkeypatch.setattr("services.prompt_templates.execute_prompt_template", _fake)
    return calls


VALID = json.dumps(
    {
        "results": [
            {
                "target_key": "a",
                "matched_name": "GPT-4.1",
                "pricing_options": [{"label": "Global", "price_input": "2"}],
            }
        ]
    }
)


class TestExtractModelsFromText:
    @pytest.mark.anyio
    async def test_happy_path(self, monkeypatch):
        _patch_template(monkeypatch, _template())
        calls = _patch_execute(monkeypatch, [f"```json\n{VALID}\n```"])

        response = await svc.extract_models_from_text(_request())

        assert [r.matched_name for r in response.results] == ["GPT-4.1", None]
        call = calls[0]
        assert call["system_name_or_config"]["response_format"]["type"] == "json_schema"
        assert (
            json.loads(call["template_values"]["targets"])[0]["ai_model"] == "gpt-4.1"
        )
        assert call["template_values"]["provider"] == "Azure"
        assert call["template_additional_messages"] == [
            {"role": "user", "content": "### Source 1\npricing page"}
        ]

    @pytest.mark.anyio
    async def test_retries_once_with_errors(self, monkeypatch):
        _patch_template(monkeypatch, _template())
        calls = _patch_execute(monkeypatch, ["None", VALID])

        response = await svc.extract_models_from_text(_request())

        assert response.results[0].matched_name == "GPT-4.1"
        retry_messages = calls[1]["template_additional_messages"]
        assert [m["role"] for m in retry_messages] == ["user", "assistant", "user"]
        assert "did not validate" in retry_messages[-1]["content"]

    @pytest.mark.anyio
    async def test_gives_up_after_retry(self, monkeypatch):
        _patch_template(monkeypatch, _template())
        _patch_execute(monkeypatch, ['{"results": "x"}', "garbage"])

        with pytest.raises(svc.ModelExtractionError) as err:
            await svc.extract_models_from_text(_request())
        assert err.value.status_code == 502

    @pytest.mark.anyio
    async def test_falls_back_to_json_object(self, monkeypatch):
        _patch_template(monkeypatch, _template())
        calls = _patch_execute(
            monkeypatch,
            [RuntimeError("response_format json_schema unsupported"), VALID],
        )

        await svc.extract_models_from_text(_request())

        formats = [c["system_name_or_config"]["response_format"] for c in calls]
        assert formats[-1] == {"type": "json_object"}

    @pytest.mark.anyio
    async def test_missing_template(self, monkeypatch):
        _patch_template(monkeypatch, LookupError("not found"))

        with pytest.raises(svc.ModelExtractionError) as err:
            await svc.extract_models_from_text(_request())
        assert err.value.status_code == 422
        assert svc.MODEL_EXTRACTION_PROMPT_TEMPLATE in str(err.value)

    @pytest.mark.anyio
    async def test_template_without_model(self, monkeypatch):
        _patch_template(monkeypatch, _template(system_name_for_model=None))

        with pytest.raises(svc.ModelExtractionError) as err:
            await svc.extract_models_from_text(_request())
        assert err.value.status_code == 422

    @pytest.mark.anyio
    async def test_missing_model_on_template(self, monkeypatch):
        _patch_template(monkeypatch, _template())
        _patch_execute(monkeypatch, [LookupError("Model GPT not found")])

        with pytest.raises(svc.ModelExtractionError) as err:
            await svc.extract_models_from_text(_request())
        assert err.value.status_code == 422
