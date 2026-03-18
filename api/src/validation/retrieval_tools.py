from pydantic import BaseModel, Field

from type_defs.pagination import FilterObject
from validation.rag_tools import LanguageConfig, RetrieveConfig, UISettingsConfig


class RetrievalToolsBase(BaseModel):
    retrieve: RetrieveConfig
    ui_settings: UISettingsConfig | None = Field(default_factory=UISettingsConfig)
    language: LanguageConfig | None = None
    sample_test_set: str | None = None
    variant: str = Field(description="variant name")
    description: str | None = None


class RetrievalToolsConfig(BaseModel):
    variants: list[RetrievalToolsBase] = Field(description="list of variants")
    active_variant: str = Field(description="active variant")
    system_name: str = Field(description="tag tool system name")
    name: str = Field(description="tag tool name")
    description: str | None = None


class RetrievalToolTest(RetrievalToolsBase):
    user_message: str = Field(
        description="User's message to the RAG tool",
        examples=["How to ...?"],
    )
    metadata_filter: FilterObject | None = Field(
        description="MongoDB-like filter to narrow down knowledge source chunks. Supported operators: $eq, $ne, $in, $nin, $exists, $regex, $txt.",
        default=None,
        examples=[{"$and": [{"language": {"$eq": "en"}}]}],
    )
    name: str | None = None


class RetrievalToolExecute(BaseModel):
    system_name: str = Field(
        description="Retrieval Tool system name",
        examples=["FAQ_TOOL"],
    )
    user_message: str = Field(
        description="User's message to the RAG tool",
        examples=["How to ...?"],
    )
    metadata_filter: FilterObject | None = Field(
        description="MongoDB-like filter to narrow down knowledge source chunks. Supported operators: $eq, $ne, $in, $nin, $exists, $regex, $txt.",
        default=None,
        examples=[{"$and": [{"language": {"$eq": "en"}}]}],
    )
    name: str | None = None
