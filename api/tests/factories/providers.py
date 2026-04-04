"""Provider factories."""

from __future__ import annotations

import factory

from core.db.models.provider import Provider

from .base import BaseFactory


class ProviderFactory(BaseFactory):
    class Meta:
        model = Provider

    name = factory.Sequence(lambda n: f"Provider {n}")
    system_name = factory.Sequence(lambda n: f"provider-{n}")
    description = factory.Faker("sentence")
    type = "openai"
    endpoint = "https://api.openai.com/v1"
    connection_config = factory.LazyFunction(dict)
    secrets_encrypted = factory.LazyFunction(dict)
