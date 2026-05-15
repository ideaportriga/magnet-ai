"""Pydantic mixin that adds tenant + record-level fields to entity schemas.

Pair with `services.access_control.attach_permissions` in the controller —
the controller computes `_permissions`, the mixin handles wire-format
renaming + UUID→str coercion. Used by every tenant-scoped entity schema
in the PR 10 rollout (collections, prompts, ai_apps, ...).
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_serializer


class RecordLevelFieldsMixin(BaseModel):
    """Adds tenant_id / owner_id / department_id / visibility / _permissions.

    Sibling-class to the base entity schemas in `core.domain.base.schemas`.
    Pure shape — no business logic. Attaching `permissions` is the
    controller's job (`attach_permissions` from `services.access_control`).
    """

    model_config = ConfigDict(populate_by_name=True)

    tenant_id: Optional[str] = Field(default=None, description="Owning tenant id")
    owner_id: Optional[str] = Field(default=None, description="Owner user id")
    department_id: Optional[str] = Field(
        default=None, description="Owning department id"
    )
    visibility: Optional[str] = Field(
        default="tenant",
        description="'private' | 'department' | 'tenant'",
    )
    permissions: Optional[dict[str, bool]] = Field(
        default=None,
        alias="_permissions",
        serialization_alias="_permissions",
        description="Per-record action flags (view/edit/delete/share)",
    )

    @field_validator("tenant_id", "owner_id", "department_id", mode="before")
    @classmethod
    def _stringify_uuid(cls, value):
        if isinstance(value, UUID):
            return str(value)
        return value

    @model_serializer(mode="wrap")
    def _rename_permissions_field(self, handler):
        """Emit `permissions` as `_permissions` on the wire.

        Pydantic's `serialization_alias` only fires when `by_alias=True` is
        passed to `model_dump` — Litestar's default serializer doesn't.
        This wrap renames the key after the default dump runs.
        """
        result = handler(self)
        if isinstance(result, dict) and "permissions" in result:
            result["_permissions"] = result.pop("permissions")
        return result
