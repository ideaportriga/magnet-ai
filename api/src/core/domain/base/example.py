"""
Example of minimal entity using base schemas.

This shows the simplest possible usage of base schemas for a new entity.
"""

from __future__ import annotations

from core.domain.base import (
    BaseEntityCreateSchema,
    BaseEntitySchema,
    BaseEntityUpdateSchema,
)


# Minimal entity schemas - inherit everything from base
class ExampleEntity(BaseEntitySchema):
    """Example entity schema using only base fields."""


class ExampleEntityCreate(BaseEntityCreateSchema):
    """Schema for creating example entity."""


class ExampleEntityUpdate(BaseEntityUpdateSchema):
    """Schema for updating example entity."""


# Example service (uncomment when you have the SQLAlchemy model)
#
# from advanced_alchemy.extensions.litestar import repository, service
#
# class ExampleEntityService(service.SQLAlchemyAsyncRepositoryService[ExampleEntityModel]):
#     """Example entity service."""
#
#     class Repo(repository.SQLAlchemyAsyncRepository[ExampleEntityModel]):
#         """Example entity repository."""
#         model_type = ExampleEntityModel
#
#     repository_type = Repo
