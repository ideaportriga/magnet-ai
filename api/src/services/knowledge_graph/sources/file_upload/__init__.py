"""File Upload -> Knowledge Graph source.

This source is a specialized ingestion entrypoint used for manual file uploads.
Unlike other sources (SharePoint/Fluid Topics), it does not implement `sync_source`;
instead it exposes a dedicated method that:
- validates the upload against content configs
- loads content from raw bytes
- creates/updates the per-graph document + chunks
"""

from .file_upload_source import FileUploadDataSource

__all__ = [
    "FileUploadDataSource",
]
