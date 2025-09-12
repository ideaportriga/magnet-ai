from dataclasses import dataclass

from pydantic import BaseModel, Field


@dataclass
class RightNowConfig:
    username: str
    password: str


class Link(BaseModel):
    rel: str
    href: str


class Answer(BaseModel):
    id: int
    created_time: str = Field(alias="createdTime")
    updated_time: str = Field(alias="updatedTime")
    question: str | None
    solution: str | None
    summary: str | None


class AnswersResponse(BaseModel):
    items: list[Answer]
    has_more: bool = Field(alias="hasMore")
    links: list[Link]
