"""Evaluation results carry usage (incl. cached tokens) and cost."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

# Prime config before importing the v1 observability package to avoid the
# circular import (same preamble as ``test_observability_cost_details``).
import core.config.app  # noqa: F401  isort:skip
from services.jobs.jobs_types import evaluate  # noqa: E402
from services.observability.models import (  # noqa: E402
    CostDetails,
    UsageDetails,
    UsageInputDetails,
)
from services.observability.usage_collector import record_llm_usage  # noqa: E402


def _usage(prompt: int, completion: int, cached: int | None) -> UsageDetails:
    return UsageDetails(
        input=prompt,
        output=completion,
        input_details=UsageInputDetails(cached=cached),
    )


@pytest.mark.anyio
async def test_rag_eval_sums_usage_and_cost_of_its_llm_calls(monkeypatch):
    async def _rag_tool(**_kwargs):
        # e.g. an embedding call and the generation call
        record_llm_usage(_usage(20, 0, None), CostDetails(total=0.001))
        record_llm_usage(_usage(1_000, 200, 600), CostDetails(total=0.01))
        return "answer"

    monkeypatch.setattr(evaluate, "execute_test_set_item_rag_tool", _rag_tool)

    result = await evaluate.evaluate_record(
        evaluate.JobType.RAG_EVAL, "tool", None, {}, None, "question"
    )

    assert result["answer"] == "answer"
    assert result["usage"] == {
        "prompt_tokens": 1_020,
        "completion_tokens": 200,
        "cached_tokens": 600,
    }
    assert result["cost"] == pytest.approx(0.011)


@pytest.mark.anyio
async def test_prompt_eval_records_cached_tokens(monkeypatch):
    completion = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="answer"))],
        usage=SimpleNamespace(prompt_tokens=6_724, completion_tokens=299),
        usage_details=_usage(6_724, 299, 6_698),
        cost_details=CostDetails(total=0.0089),
        model="gpt-5.6",
    )

    async def _template(*_args, **_kwargs):
        return {}

    async def _chat(**_kwargs):
        return completion, []

    monkeypatch.setattr(evaluate, "get_prompt_template_by_system_name_flat", _template)
    monkeypatch.setattr(evaluate, "create_chat_completion_from_prompt_template", _chat)

    result = await evaluate.evaluate_record(
        evaluate.JobType.PROMPT_EVAL, "prompt", None, {}, None, "question"
    )

    assert result["usage"] == {
        "prompt_tokens": 6_724,
        "completion_tokens": 299,
        "cached_tokens": 6_698,
    }
    assert result["cost"] == pytest.approx(0.0089)
