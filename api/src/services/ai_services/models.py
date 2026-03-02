from dataclasses import dataclass, field
from typing import Any

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


@dataclass
class RoutingConfig:
    """Typed representation of AIModel.routing_config.

    Provides IDE autocompletion and catches typos at development time
    instead of silent runtime failures with dict key misses.
    """

    rpm: int | None = None
    tpm: int | None = None
    fallback_models: list[str] = field(default_factory=list)
    cache_enabled: bool = False
    cache_ttl: int = 3600
    num_retries: int | None = None
    retry_after: int | None = None
    timeout: int | None = None
    priority: int | None = None
    weight: int | None = None
    litellm_params: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "RoutingConfig":
        """Create RoutingConfig from a raw dict (e.g. from DB JSON column).

        Unknown keys are silently ignored so the DB schema can evolve
        without breaking existing code.
        """
        if not data:
            return cls()

        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered)
