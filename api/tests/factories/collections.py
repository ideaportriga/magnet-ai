"""Collection factories."""

from __future__ import annotations

import factory

from core.db.models.collection import Collection

from .base import BaseFactory


class CollectionFactory(BaseFactory):
    class Meta:
        model = Collection

    name = factory.Sequence(lambda n: f"Collection {n}")
    system_name = factory.Sequence(lambda n: f"collection-{n}")
    description = factory.Faker("sentence")
    type = "documents"
    source = factory.LazyFunction(dict)
    chunking = factory.LazyFunction(dict)
    indexing = factory.LazyFunction(dict)
