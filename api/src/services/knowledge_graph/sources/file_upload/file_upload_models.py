from dataclasses import dataclass
from typing import Any

from ...models import ContentConfig


@dataclass(frozen=True)
class FileUploadListingTask:
    """Placeholder listing task type.

    File uploads do not use the listing queue; tasks are seeded directly into the
    content-fetch queue via the pipeline bootstrap hook.
    """


@dataclass(frozen=True)
class FileUploadContentFetchTask:
    """Task for the content-fetch stage (we already have the bytes)."""

    filename: str
    file_bytes: bytes
    content_config: ContentConfig


@dataclass(frozen=True)
class FileUploadProcessDocumentTask:
    """Task for the long-running document-processing stage."""

    document: dict[str, Any]
    extracted_text: str
    content_config: ContentConfig
