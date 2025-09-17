from pydantic import BaseModel, Field, RootModel


class MetadataAutomapRequest(BaseModel):
    exclude_fields: list[str] | None = Field(default=None)


class MetadataAutomapField(BaseModel):
    enabled: bool = Field(default=True)
    name: str = Field()
    mapping: str = Field()


class MetadataAutomapResponse(RootModel):
    root: dict[str, MetadataAutomapField]
