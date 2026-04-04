"""User, Role, Group factories."""

from __future__ import annotations

import factory

from core.db.models.user import Group, Role, User

from .base import BaseFactory


class UserFactory(BaseFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user-{n}@test.magnet.ai")
    name = factory.Faker("name")
    is_active = True
    is_superuser = False
    is_verified = False


class RoleFactory(BaseFactory):
    class Meta:
        model = Role

    name = factory.Sequence(lambda n: f"Role {n}")
    slug = factory.Sequence(lambda n: f"role-{n}")
    description = factory.Faker("sentence")


class GroupFactory(BaseFactory):
    class Meta:
        model = Group

    name = factory.Sequence(lambda n: f"Group {n}")
    slug = factory.Sequence(lambda n: f"group-{n}")
    description = factory.Faker("sentence")
