from dataclasses import dataclass


@dataclass
class BasicMetadata:
    title: str
    modified_date: str


@dataclass
class SourceBasicMetadata(BasicMetadata):
    source_id: str


@dataclass
class DocumentBasicMetadata(BasicMetadata):
    document_id: str
