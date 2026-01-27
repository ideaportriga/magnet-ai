from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class SharePointLibrary(StrEnum):
    """SharePoint library types."""

    PAGES = "SitePages"
    DOCUMENTS = "Shared Documents"


# SharePoint automatically creates these system folders in every library.
# They contain UI elements and system files that:
# 1. Cannot be downloaded via the API (403 Forbidden)
# 2. Should not be indexed as content
# Reference: Standard SharePoint library structure
SHAREPOINT_SYSTEM_FOLDERS = {
    "Forms",  # List view forms: DispForm.aspx, EditForm.aspx, NewForm.aspx, AllItems.aspx
    "_catalogs",  # Master pages, themes, web parts catalogs
    "_private",  # System private files
    "Style Library",  # Themes, CSS, images for site styling
    "_layouts",  # SharePoint layouts and system pages
}


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
    unique_id: str | None = None
    time_last_modified: str | None = None  # ISO format datetime string


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
    external_link: str | None = None


@dataclass
class SharePointSharedSyncState:
    """Per-sync-run shared state between SharePoint workers."""

    queued_folders: set[str] = field(default_factory=set)
    processed_folders: set[str] = field(default_factory=set)
    folders_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    # Track all source_document_ids seen during listing for orphan cleanup
    seen_source_document_ids: set[str] = field(default_factory=set)
    seen_ids_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
