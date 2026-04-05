from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class WebRuntimeConfig:
    """Resolved web scraper configuration for a single sync run."""

    url: str
    follow_links: bool = False
    max_depth: int = 2
    max_pages: int = 100
    css_selector: str | None = None
    allowed_domain: str = ""


@dataclass(frozen=True)
class WebListingTask:
    """Task for the listing stage: discover and fetch a URL."""

    url: str
    depth: int = 0


@dataclass(frozen=True)
class WebContentFetchTask:
    """Task for the content-fetch stage: store document from fetched HTML."""

    url: str
    title: str
    text_content: str


@dataclass(frozen=True)
class WebProcessDocumentTask:
    """Task for the document-processing stage: chunk + embed."""

    document: dict[str, Any]
    extracted_text: str
    raw_text: str | None = None
    content_config: Any | None = None
    external_link: str | None = None


@dataclass
class WebSharedSyncState:
    """Per-sync-run shared state between web scraper workers."""

    visited_urls: set[str] = field(default_factory=set)
    urls_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    pages_count: int = 0
