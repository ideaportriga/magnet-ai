"""Sum the usage and cost of every v1 LLM call made inside a block.

A feature that makes several model calls (a RAG tool: translation, embeddings,
rerank, generation) doesn't return their cost. Wrapping it in
:func:`collect_llm_usage` gathers what each call already reports through
``observability_context.record_llm_metrics``:

    with collect_llm_usage() as collected:
        await execute_rag_tool(...)
    collected.cost  # summed USD, None when no call was priced
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass

from services.observability.models import CostDetails, UsageDetails


@dataclass
class CollectedLLMUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cached_tokens: int = 0
    #: ``None`` until a call reports a cost, so "unpriced" stays distinct from $0.
    cost: float | None = None

    def add(self, usage: UsageDetails | None, cost: CostDetails | None) -> None:
        if usage is not None:
            self.prompt_tokens += usage.input or 0
            self.completion_tokens += usage.output or 0
            if usage.input_details is not None:
                self.cached_tokens += usage.input_details.cached or 0
        if cost is not None and cost.total is not None:
            self.cost = (self.cost or 0.0) + cost.total


_collectors: ContextVar[tuple[CollectedLLMUsage, ...]] = ContextVar(
    "llm_usage_collectors", default=()
)


@contextmanager
def collect_llm_usage() -> Iterator[CollectedLLMUsage]:
    """Collect the usage/cost of LLM calls in this block (nests: outer sees all)."""
    collected = CollectedLLMUsage()
    token = _collectors.set((*_collectors.get(), collected))
    try:
        yield collected
    finally:
        _collectors.reset(token)


def record_llm_usage(usage: UsageDetails | None, cost: CostDetails | None) -> None:
    """Add one call's usage/cost to every active collector (no-op without one)."""
    for collected in _collectors.get():
        collected.add(usage, cost)
