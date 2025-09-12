from pydantic import BaseModel, Field

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
    name: str | None = None


class RetrievalToolExecute(BaseModel):
    user_message: str = Field(
        description="User's message to the RAG tool",
        examples=["How to ...?"],
    )
    system_name: str = Field(
        description="Retrieval Tool system name",
        examples=["FAQ_TOOL"],
    )
    name: str | None = None
