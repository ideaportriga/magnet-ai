"""Base factory for all model factories."""

from __future__ import annotations

from factory.alchemy import SQLAlchemyModelFactory


class BaseFactory(SQLAlchemyModelFactory):
    """Base factory with common settings for all models.

    The SQLAlchemy session is injected per-test via the
    ``_bind_factory_session`` fixture in conftest.py.
    """

    class Meta:
        abstract = True
        sqlalchemy_session_persistence = "flush"
