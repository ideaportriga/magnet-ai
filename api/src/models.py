from dataclasses import dataclass
from decimal import Decimal


@dataclass
class Prompt:
    id: int
    name: str
    text: str
    description: str
    iconName: str
    pinned: int
    model: str
    temperature: Decimal
    topP: Decimal


@dataclass(kw_only=True)
class DocumentData:
    content: str
    metadata: dict


# TODO - rename to DocumentSimilaritySearchResultItem?
@dataclass(kw_only=True)
class DocumentSearchResultItem(DocumentData):
    id: str
    score: Decimal
    completion: bool = False  # TODO - remove after Q&A will be removed
    collection_id: str
    original_index: int | None = None


DocumentSearchResult = list[DocumentSearchResultItem]


@dataclass(kw_only=True)
class Document(DocumentData):
    id: str


QueryChunksByCollectionBySource = dict[str, dict[str, list[int]]]


ChunksByCollection = dict[str, list[dict]]
