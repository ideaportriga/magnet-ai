import asyncio
from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class FluidTopicsRuntimeConfig:
    """Resolved configuration for a single sync run (provider + source overrides)."""

    api_key: str
    search_api_url: str
    pdf_api_url: str | None
    map_content_url_template: str | None
    map_toc_url_template: str | None
    filters: list[Any]


@dataclass(frozen=True)
class FluidTopicsListingTask:
    """Task for the listing stage (pagination over Fluid Topics search results)."""

    page: int


@dataclass(frozen=True)
class FluidTopicsContentFetchTask:
    """Task for the content-fetch stage (topic map or file bytes)."""

    kind: Literal["map", "document"]
    map_id: str | None = None
    map_title: str | None = None
    filename: str | None = None


@dataclass(frozen=True)
class ProcessDocumentTask:
    """Task for the long-running document-processing stage."""

    document: dict[str, Any]

    # Map mode (pre-chunked)
    chunks: list[dict[str, Any]] | None = None
    toc: list[dict[str, Any]] | None = None
    document_title: str | None = None

    # Document mode (split)
    extracted_text: str | None = None
    content_config: Any | None = None


@dataclass
class FluidTopicsSharedSyncState:
    """Per-sync-run shared state between Fluid Topics workers."""

    seen_maps: dict[str, str] = field(default_factory=dict)
    seen_maps_lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    pages_done: asyncio.Event = field(default_factory=asyncio.Event)
