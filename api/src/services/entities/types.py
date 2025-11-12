from datetime import datetime
from typing import Generic, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field


class BaseEntity(BaseModel):
    id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    name: str
    description: Optional[str] = None
    system_name: str
    category: Optional[str] = None


VariantValueType = TypeVar("VariantValueType", bound=BaseModel)


class EntityVariant(BaseModel, Generic[VariantValueType]):
    variant: str
    description: str | None = None
    value: VariantValueType


VariantType = TypeVar("VariantType", bound=EntityVariant)


class BaseEntityMultiVariant(BaseEntity, Generic[VariantValueType]):
    variants: list[EntityVariant[VariantValueType]] = Field(
        description="List of variants",
    )
    active_variant: str = Field(description="Active variant")

    @property
    def active_variant_value(self) -> VariantValueType:
        """Retrieve the active variant from the current model."""
        for variant in self.variants:
            if variant.variant == self.active_variant:
                return variant.value

        raise ValueError("Active variant data missing")
