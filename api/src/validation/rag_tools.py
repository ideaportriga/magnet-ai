import re
from datetime import datetime

from pydantic import BaseModel, Field, root_validator


# RAG CRUD operations input validation
# TODO - rename so that it's not post process specific?
class PostProcessPromptConfig(BaseModel):
    enabled: bool = Field(default=False)
    prompt_template: str = Field(default="")


class CategorizationConfig(BaseModel):
    enabled: bool = False
    prompt_template: str = ""
    categories: list[str] = Field(default_factory=list)


class RerankConfig(BaseModel):
    enabled: bool = Field(default=False)
    model: str = Field(default="")
    top_n: int = Field(default=5)
    return_documents: bool = Field(default=False)
    truncation: bool = Field(default=False)
    max_chunks_retrieved: int = Field(default=5, ge=0, le=50)


class RetrieveConfig(BaseModel):
    collection_system_names: list[str] = Field(
        description="list of collection system names",
    )
    similarity_score_threshold: float = Field(
        ge=0.0,
        le=1.0,
        description="similarity score",
    )
    max_chunks_retrieved: int = Field(default=5, ge=0, le=50)
    chunk_context_window_expansion_size: int = Field(default=1, ge=0, le=10)
    rerank: RerankConfig | None = Field(default_factory=RerankConfig)


class GenerateConfig(BaseModel):
    prompt_template: str = Field(description="prompt template system name")


class PostProcessConfig(BaseModel):
    answered_check: PostProcessPromptConfig = Field(
        default_factory=PostProcessPromptConfig,
    )
    detect_question_language: PostProcessPromptConfig = Field(
        default_factory=PostProcessPromptConfig,
    )
    check_is_hallucinate: PostProcessPromptConfig = Field(
        default_factory=PostProcessPromptConfig,
    )
    categorization: CategorizationConfig = Field(default_factory=CategorizationConfig)
    enabled: bool = Field(default=False)


class HeaderConfiguration(BaseModel):
    header: str = Field(default="")
    sub_header: str = Field(default="")


class SampleQuestions(BaseModel):
    enabled: bool = Field(default=False)
    questions: dict[str, str] = Field(default_factory=dict)

    @root_validator(pre=True)
    def check_questions(cls, values):
        questions = values.get("questions", {})
        if len(questions) > 10:
            raise ValueError("No more than 10 questions are allowed.")
        for key in questions.keys():
            if not re.match(r"^question\d+$", key):
                raise ValueError(
                    f"Invalid question name: {key}. Must be in the format 'question' followed by a number.",
                )
        return values


class UISettingsConfig(BaseModel):
    header_configuration: HeaderConfiguration = Field(
        default_factory=HeaderConfiguration,
    )
    user_fideback: bool = Field(default=False)
    show_link_titles: bool = Field(default=False)
    offer_to_bypass_cache: bool = Field(default=False)
    sample_questions: SampleQuestions = Field(default_factory=SampleQuestions)


class MultilanguageConfig(BaseModel):
    enabled: bool = False
    source_language: str
    prompt_template_translation: str


class LanguageConfig(BaseModel):
    detect_question_language: PostProcessPromptConfig = Field(
        default_factory=PostProcessPromptConfig,
    )
    multilanguage: MultilanguageConfig


class RagToolsBase(BaseModel):
    retrieve: RetrieveConfig
    generate: GenerateConfig
    post_process: PostProcessConfig | None = Field(default_factory=PostProcessConfig)
    ui_settings: UISettingsConfig | None = Field(default_factory=UISettingsConfig)
    sample_test_set: str | None = None
    language: LanguageConfig | None = None
    variant: str = Field(description="variant name")
    description: str | None = None


# RAG tool test input validation


class RagToolsConfig(BaseModel):
    variants: list[RagToolsBase] = Field(description="list of variants")
    active_variant: str = Field(description="active variant")
    system_name: str = Field(description="tag tool system name")
    name: str = Field(description="tag tool name")
    description: str | None = None


class RagToolTest(RagToolsBase):
    user_message: str = Field(
        description="User's message to the RAG tool",
        examples=["How to ...?"],
    )
    system_name: str = Field(
        description="RAG Tool system name",
        examples=["FAQ_TOOL"],
    )


class RagToolExecute(BaseModel):
    user_message: str = Field(
        description="User's message to the RAG tool",
        examples=["How to ...?"],
    )
    system_name: str = Field(
        description="RAG Tool system name",
        examples=["FAQ_TOOL"],
    )


# Search response validation


class Metadata(BaseModel):
    createdTime: datetime
    loc: str
    modifiedTime: datetime
    source: str
    title: str


class Result(BaseModel):
    collection_id: str
    completion: bool
    content: str
    metadata: Metadata
    score: float
