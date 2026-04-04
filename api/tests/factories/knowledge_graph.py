"""Knowledge Graph factories."""

from __future__ import annotations

import factory

from core.db.models.knowledge_graph import KnowledgeGraph, KnowledgeGraphSource

from .base import BaseFactory


class KnowledgeGraphFactory(BaseFactory):
    class Meta:
        model = KnowledgeGraph

    name = factory.Sequence(lambda n: f"KG {n}")
    system_name = factory.Sequence(lambda n: f"kg-{n}")
    description = factory.Faker("sentence")
    settings = factory.LazyFunction(dict)
    state = factory.LazyFunction(dict)


class KnowledgeGraphSourceFactory(BaseFactory):
    class Meta:
        model = KnowledgeGraphSource

    name = factory.Sequence(lambda n: f"KG Source {n}")
    graph_id = factory.LazyAttribute(
        lambda o: o.graph.id if hasattr(o, "graph") else None
    )
    type = "upload"
    config = factory.LazyFunction(dict)
    status = "idle"
