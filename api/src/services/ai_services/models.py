from dataclasses import dataclass

from models import DocumentSearchResult


@dataclass
class ModelUsage:
    input_units: str
    input: int
    total: int


@dataclass
class EmbeddingResponse:
    data: list[float]
    usage: ModelUsage


@dataclass
class RerankResponse:
    data: DocumentSearchResult
    usage: ModelUsage | None
