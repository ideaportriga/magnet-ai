"""Registry of entities exposed to the AI editor.

Each descriptor binds an entity slug (the same one used by the audit
registry — ``"agent"``, ``"prompt_template"``, …) to:

* the SQLAlchemy ORM model (so the service can read the current state),
* the Pydantic model that describes the **editable** subset of the
  entity (this is what the LLM is constrained to produce — usually the
  ``*VariantValue`` body, not the whole DB row),
* a short human-readable description that goes into the system prompt
  to give the LLM context about what kind of object it's editing,
* the write permission required to call the endpoint,
* extra forbidden paths (server-controlled fields like ``tenant_id`` /
  ``owner_id`` are always stripped).

Registration is explicit so we can scope the AI surface to entities
we've actually validated end-to-end.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar, Literal, Type

from guards.permissions import Permission

if TYPE_CHECKING:
    from pydantic import BaseModel
    from sqlalchemy.orm import DeclarativeBase


# These columns are never supplied by the LLM. Mirrors the audit
# descriptor's forbidden-fields default (kept in sync deliberately so the
# AI editor can never push values that the controller would reject anyway).
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
class AIEditableDescriptor:
    entity_type: str
    resource_type: str
    model: Type["DeclarativeBase"]
    editable_schema: Type["BaseModel"]
    human_description: str
    write_permission: Permission
    variant_shape: Literal["entity", "wrapped", "flat"] = "entity"
    extra_forbidden: frozenset[str] = field(default_factory=frozenset)

    @property
    def forbidden_fields(self) -> frozenset[str]:
        return _DEFAULT_FORBIDDEN | self.extra_forbidden


class _AIEditRegistry:
    _by_type: ClassVar[dict[str, AIEditableDescriptor]] = {}

    @classmethod
    def register(cls, descriptor: AIEditableDescriptor) -> None:
        cls._by_type[descriptor.entity_type] = descriptor

    @classmethod
    def get(cls, entity_type: str) -> AIEditableDescriptor | None:
        return cls._by_type.get(entity_type)

    @classmethod
    def all_types(cls) -> list[str]:
        return sorted(cls._by_type.keys())


def register_ai_editable(
    entity_type: str,
    model: Type["DeclarativeBase"],
    editable_schema: Type["BaseModel"],
    *,
    resource_type: str,
    human_description: str,
    write_permission: Permission,
    variant_shape: Literal["entity", "wrapped", "flat"] = "entity",
    extra_forbidden: frozenset[str] = frozenset(),
) -> None:
    """Register an entity type for the AI editor endpoint."""
    _AIEditRegistry.register(
        AIEditableDescriptor(
            entity_type=entity_type,
            resource_type=resource_type,
            model=model,
            editable_schema=editable_schema,
            human_description=human_description,
            write_permission=write_permission,
            variant_shape=variant_shape,
            extra_forbidden=extra_forbidden,
        )
    )


def get_ai_editable(entity_type: str) -> AIEditableDescriptor | None:
    return _AIEditRegistry.get(entity_type)


def ai_editable_types() -> list[str]:
    return _AIEditRegistry.all_types()
