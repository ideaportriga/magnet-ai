"""Job factories."""

from __future__ import annotations

import factory

from core.db.models.job import Job

from .base import BaseFactory


class JobFactory(BaseFactory):
    class Meta:
        model = Job

    status = "pending"
    definition = factory.LazyFunction(lambda: {"type": "test", "config": {}})
