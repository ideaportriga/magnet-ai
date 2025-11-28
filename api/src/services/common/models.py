from enum import StrEnum

from pydantic import BaseModel


class EmptyDictionary(BaseModel):
    pass


class LlmResponseFeedbackType(StrEnum):
    LIKE = "like"
    DISLIKE = "dislike"


class LlmResponseFeedbackReason(StrEnum):
    NOT_RELEVANT = "not_relevant"
    INACCURATE = "inaccurate"
    OUTDATED = "outdated"
    OTHER = "other"


class LlmResponseFeedback(BaseModel):
    type: LlmResponseFeedbackType
    reason: LlmResponseFeedbackReason | None = None
    comment: str | None = None


class ConversationMessageFeedback(BaseModel):
    reason: str | None = None
    comment: str | None = None
