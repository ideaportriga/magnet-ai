"""Evaluation and EvaluationSet factories."""

from __future__ import annotations

import factory

from core.db.models.evaluation import Evaluation
from core.db.models.evaluation_set import EvaluationSet

from .base import BaseFactory


class EvaluationFactory(BaseFactory):
    class Meta:
        model = Evaluation

    status = "pending"
    type = "rag"
    test_sets = factory.LazyFunction(list)
    results = factory.LazyFunction(dict)


class EvaluationSetFactory(BaseFactory):
    class Meta:
        model = EvaluationSet

    name = factory.Sequence(lambda n: f"Eval Set {n}")
    system_name = factory.Sequence(lambda n: f"eval-set-{n}")
    type = "rag"
    items = factory.LazyFunction(
        lambda: [
            {"question": "What is AI?", "expected_answer": "Artificial Intelligence"}
        ]
    )
