"""Prompt factories."""

from __future__ import annotations

import factory

from core.db.models.prompt import Prompt

from .base import BaseFactory


class PromptFactory(BaseFactory):
    class Meta:
        model = Prompt

    name = factory.Sequence(lambda n: f"Prompt {n}")
    system_name = factory.Sequence(lambda n: f"prompt-{n}")
    description = factory.Faker("sentence")
    active_variant = "default"
    variants = factory.LazyFunction(
        lambda: [{"name": "default", "template": "Hello, {name}!"}]
    )
