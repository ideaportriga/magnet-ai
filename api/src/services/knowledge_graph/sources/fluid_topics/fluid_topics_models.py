import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from core.db.models.knowledge_graph import KnowledgeGraphChunk


@dataclass(frozen=True)
class FluidTopicsRuntimeConfig:
    """Resolved configuration for a single sync run (provider + source overrides)."""

    api_key: str
    search_api_url: str
    pdf_api_url: str | None
    map_content_url_template: str | None
    map_toc_url_template: str | None
    map_structure_url_template: str | None
    filters: list[Any]


@dataclass(frozen=True)
class FluidTopicsListingTask:
    """Task for the listing stage (pagination over Fluid Topics search results)."""

    page: int


@dataclass(frozen=True)
class FluidTopicsContentFetchTask:
    """Task for the content-fetch stage (topic map or file bytes)."""

    id: str
    title: str | None = None
    metadata: dict[str, Any] | None = None
    last_edition_date: str | None = None
    external_link: str | None = None


@dataclass(frozen=True)
class FluidTopicsDocumentFetchTask(FluidTopicsContentFetchTask):
    filename: str | None = None


@dataclass(frozen=True)
class FluidTopicsMapFetchTask(FluidTopicsContentFetchTask):
    # If true, map metadata should be fetched from the configured map-structure endpoint
    # (used for TOPIC entries where search results don't contain map metadata).
    metadata_from_structure: bool = False


@dataclass(frozen=True)
class ProcessDocumentTask:
    """Task for the long-running document-processing stage."""

    document: dict[str, Any]

    # Map mode (pre-chunked)
    chunks: list[KnowledgeGraphChunk] | None = None
    toc: list[dict[str, Any]] | None = None
    document_title: str | None = None

    # Document mode (split)
    extracted_text: str | None = None
    raw_text: str | None = None
    content_config: Any | None = None
    external_link: str | None = None
    source_modified_at: datetime | None = None


@dataclass
class FluidTopicsSharedSyncState:
    """Per-sync-run shared state between Fluid Topics workers."""

    seen_maps: dict[str, str] = field(default_factory=dict)
    seen_maps_lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    pages_done: asyncio.Event = field(default_factory=asyncio.Event)
