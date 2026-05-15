"""User, Role, Group factories."""

from __future__ import annotations

import factory

from core.db.models.user import Group, Role, User

from .base import BaseFactory


def _resolve_default_tenant_id():
    """Look up the seeded default tenant id from the bound factory session.

    Runs synchronously via greenlet bridge because factory_boy is sync.
    Tests that need a different tenant should pass `tenant_id=` explicitly.
    """
    from sqlalchemy import select
    from sqlalchemy.util import await_only
    from core.db.models.tenant.tenant import Tenant

    session = BaseFactory._meta.sqlalchemy_session
    result = await_only(
        session.execute(select(Tenant.id).where(Tenant.slug == "default"))
    )
    return result.scalar_one()


class UserFactory(BaseFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user-{n}@test.magnet.ai")
    name = factory.Faker("name")
    is_active = True
    is_superuser = False
    is_verified = False
    tenant_id = factory.LazyFunction(_resolve_default_tenant_id)


class RoleFactory(BaseFactory):
    """Custom (non-system) role bound to the default tenant by default."""

    class Meta:
        model = Role

    name = factory.Sequence(lambda n: f"Role {n}")
    slug = factory.Sequence(lambda n: f"role-{n}")
    description = factory.Faker("sentence")
    is_system = False
    tenant_id = factory.LazyFunction(_resolve_default_tenant_id)


class GroupFactory(BaseFactory):
    class Meta:
        model = Group

    name = factory.Sequence(lambda n: f"Group {n}")
    slug = factory.Sequence(lambda n: f"group-{n}")
    description = factory.Faker("sentence")
    tenant_id = factory.LazyFunction(_resolve_default_tenant_id)
