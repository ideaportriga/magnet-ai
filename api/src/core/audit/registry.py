"""Registry of auditable entity types.

Maps the ``entity_type`` slug stored in ``entity_audit_log`` to the
metadata needed for read & restore endpoints:

  * the SQLAlchemy model (so we can resolve / write the row)
  * the write permission required to restore
  * a set of forbidden snapshot paths that must NEVER be applied
    (server-controlled fields like ``tenant_id``, ``id``, ``created_at``)

A model is registered explicitly so the audit endpoints have a stable
contract — only known entity types can be restored.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar, Type

if TYPE_CHECKING:
    from sqlalchemy.orm import DeclarativeBase

    from guards.permissions import Permission


# Server-controlled fields. Even if a snapshot carries them, restore
# must not blindly apply them — tenant/owner/audit columns are set by
# the framework, not the user.
_DEFAULT_FORBIDDEN: frozenset[str] = frozenset(
    {
        "id",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "tenant_id",
        "owner_id",
        "sa_orm_sentinel",
    }
)


@dataclass(frozen=True)
class EntityAuditDescriptor:
    entity_type: str
    resource_type: str
    model: Type["DeclarativeBase"]
    write_permission: "Permission"
    extra_forbidden: frozenset[str] = field(default_factory=frozenset)

    @property
    def forbidden_fields(self) -> frozenset[str]:
        return _DEFAULT_FORBIDDEN | self.extra_forbidden


class _AuditRegistry:
    _by_type: ClassVar[dict[str, EntityAuditDescriptor]] = {}

    @classmethod
    def register(cls, descriptor: EntityAuditDescriptor) -> None:
        cls._by_type[descriptor.entity_type] = descriptor

    @classmethod
    def get(cls, entity_type: str) -> EntityAuditDescriptor | None:
        return cls._by_type.get(entity_type)

    @classmethod
    def all_types(cls) -> list[str]:
        return sorted(cls._by_type.keys())


def register_auditable(
    entity_type: str,
    model: Type["DeclarativeBase"],
    write_permission: "Permission",
    resource_type: str | None = None,
    extra_forbidden: frozenset[str] = frozenset(),
) -> None:
    """Register an entity type for the audit endpoints."""
    _AuditRegistry.register(
        EntityAuditDescriptor(
            entity_type=entity_type,
            resource_type=resource_type or f"{entity_type}s",
            model=model,
            write_permission=write_permission,
            extra_forbidden=extra_forbidden,
        )
    )


def get_descriptor(entity_type: str) -> EntityAuditDescriptor | None:
    return _AuditRegistry.get(entity_type)


def auditable_types() -> list[str]:
    return _AuditRegistry.all_types()
