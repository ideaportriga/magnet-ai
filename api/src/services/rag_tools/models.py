from pydantic import BaseModel


class RagToolTestResultVerboseDetails(BaseModel):
    resulting_prompt: dict | None = None


class RagToolTestResult(BaseModel):
    answer: str
    results: list
    verbose_details: RagToolTestResultVerboseDetails | None = None
    trace_id: str | None = None
    analytics_id: str | None = None


class MultilanguageContext(BaseModel):
    user_message_language: str
    user_message_original: str
    user_message_translation: str
    source_language: str
    prompt_template_translation: str
