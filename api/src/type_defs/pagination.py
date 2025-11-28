import re
from datetime import datetime
from typing import Any, Optional

from dateutil.parser import isoparse
from pydantic import BaseModel, ConfigDict, Field, RootModel, model_validator


def sanitize_regex_input(input_str: str) -> str:
    """Sanitize the input string for use in a regex."""
    return re.escape(input_str)


class FilterCondition(BaseModel):
    eq: str | int | float | bool | datetime | None = Field(None, alias="$eq")
    ne: str | int | float | bool | datetime | None = Field(None, alias="$ne")
    gt: str | int | float | bool | datetime | None = Field(None, alias="$gt")
    gte: str | int | float | bool | datetime | None = Field(None, alias="$gte")
    lt: str | int | float | bool | datetime | None = Field(None, alias="$lt")
    lte: str | int | float | bool | datetime | None = Field(None, alias="$lte")
    regex: str | None = Field(None, alias="$regex")
    options: str | None = Field(None, alias="$options")
    in_: list[str | int | float | bool | datetime | None] | None = Field(
        None,
        alias="$in",
    )
    nin: list[str | int | float | bool | datetime | None] | None = Field(
        None,
        alias="$nin",
    )
    txt: str | None = Field(None, alias="$txt")
    exists: bool | None = Field(None, alias="$exists")
    or_: list["FilterObject"] | None = Field(None, alias="$or")
    and_: list["FilterObject"] | None = Field(None, alias="$and")
    not_: Optional["FilterCondition"] = Field(None, alias="$not")

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    @model_validator(mode="before")
    def convert_datetime(cls, values: Any) -> Any:
        datetime_fields = {"$eq", "$ne", "$gt", "$gte", "$lt", "$lte"}
        list_datetime_fields = {"$in", "$nin"}
        sanitize_fields = {"$txt", "$regex"}

        def try_parse_datetime(value: Any) -> Any:
            if isinstance(value, str):
                try:
                    return isoparse(value)
                except ValueError:
                    return value
            return value

        if isinstance(values, dict):
            new_values = {}
            for key, value in values.items():
                if key in datetime_fields:
                    new_values[key] = try_parse_datetime(value)
                elif key in list_datetime_fields and isinstance(value, list):
                    new_values[key] = [try_parse_datetime(v) for v in value]
                elif key in sanitize_fields:
                    if key == "$txt":
                        new_values["$options"] = "i"
                        new_values["$regex"] = sanitize_regex_input(value)
                    else:
                        new_values["$options"] = "i"
                        new_values[key] = sanitize_regex_input(value)
                else:
                    new_values[key] = value
            return new_values
        return None


class FilterObject(RootModel[dict[str, Any]]):
    @model_validator(mode="before")
    def validate_filter_object(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            raise TypeError("FilterObject should be a dict")
        new_values = {}
        for key, value in values.items():
            if key in ("$or", "$and"):
                if not isinstance(value, list):
                    raise ValueError(f"Value for {key} should be a list")
                new_values[key] = [FilterObject.model_validate(item) for item in value]
            else:
                new_values[key] = FilterCondition.model_validate(value)
        return new_values


FilterCondition.model_rebuild()
FilterObject.model_rebuild()


class PaginationBase(BaseModel):
    limit: int
    sort: str = Field("id", description="Field for sorting")
    order: int = Field(1, description="1 = ASC, -1 = DESC")
    filters: FilterObject | None = Field(
        default_factory=lambda: FilterObject({}),
        description="Filters for search",
    )
    fields: list[str] | None = Field(None, description="List of fields to include")
    exclude_fields: list[str] | None = Field(
        None,
        description="List of fields to exclude",
    )


class CursorPaginationRequest(PaginationBase):
    cursor: str | None = Field(
        None,
        description="ID of the last item on the previous page",
    )


class OffsetPaginationRequest(PaginationBase):
    offset: int = Field(0, ge=0, description="Offset for pagination")
