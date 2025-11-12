from dataclasses import dataclass

from pydantic import BaseModel, Field


@dataclass
class ConfluenceConfig:
    username: str
    token: str


class ConfluencePageVersion(BaseModel):
    when: str


class ConfluencePageBodyStorage(BaseModel):
    value: str


class ConfluencePageBody(BaseModel):
    storage: ConfluencePageBodyStorage


class ConfluencePageHistory(BaseModel):
    created_date: str = Field(alias="createdDate")


class ConfluencePageLinks(BaseModel):
    webui: str


class ConfluencePage(BaseModel):
    id: str
    title: str
    version: ConfluencePageVersion
    body: ConfluencePageBody
    history: ConfluencePageHistory
    links: ConfluencePageLinks = Field(alias="_links")
