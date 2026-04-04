"""API Key factories."""

from __future__ import annotations

import hashlib

import factory

from core.db.models.api_key import APIKey

from .base import BaseFactory


class APIKeyFactory(BaseFactory):
    class Meta:
        model = APIKey

    name = factory.Sequence(lambda n: f"API Key {n}")
    hash = factory.LazyFunction(
        lambda: hashlib.sha256(factory.Faker("uuid4").generate()).hexdigest()
    )
    value_masked = factory.Sequence(lambda n: f"mag_...{n:04d}")
    is_active = True
