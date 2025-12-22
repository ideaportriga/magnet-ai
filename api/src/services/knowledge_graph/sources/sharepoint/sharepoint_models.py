from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SharePointRuntimeConfig:
    """Resolved SharePoint configuration for a single sync run."""

    site_url: str

    # Location
    library: str
    folder: str | None
    recursive: bool

    # Auth (either secret-based or certificate-based)
    client_id: str
    client_secret: str | None = None
    tenant: str | None = None
    thumbprint: str | None = None
    private_key: str | None = None


@dataclass(frozen=True)
class SharePointFileRef:
    """Minimal file reference used by the pipeline (not tied to a ClientContext)."""

    name: str
    server_relative_url: str


@dataclass(frozen=True)
class SharePointListingTask:
    """Task for the listing stage."""

    folder_server_relative_url: str


@dataclass(frozen=True)
class SharePointContentFetchTask:
    """Task for the content-fetch stage."""

    file: SharePointFileRef


@dataclass(frozen=True)
class ProcessDocumentTask:
    """Task for the long-running document-processing stage."""

    document: dict[str, Any]
    extracted_text: str
    content_config: Any | None = None


@dataclass
class SharePointSharedSyncState:
    """Per-sync-run shared state between SharePoint workers."""

    queued_folders: set[str] = field(default_factory=set)
    processed_folders: set[str] = field(default_factory=set)
    folders_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
