import logging
import os
from typing import Any

from kreuzberg import (
    ExtractionConfig,
    ExtractionResult,
    OcrConfig,
    PageConfig,
    extract_bytes,
)

logger = logging.getLogger(__name__)

# MIME type mapping for common file extensions
_EXTENSION_TO_MIME: dict[str, str] = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".doc": "application/msword",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".ppt": "application/vnd.ms-powerpoint",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xls": "application/vnd.ms-excel",
    ".odt": "application/vnd.oasis.opendocument.text",
    ".ods": "application/vnd.oasis.opendocument.spreadsheet",
    ".rtf": "application/rtf",
    ".html": "text/html",
    ".htm": "text/html",
    ".xml": "application/xml",
    ".json": "application/json",
    ".csv": "text/csv",
    ".tsv": "text/tab-separated-values",
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
    ".tiff": "image/tiff",
    ".tif": "image/tiff",
    ".svg": "image/svg+xml",
    ".eml": "message/rfc822",
    ".epub": "application/epub+zip",
    ".zip": "application/zip",
    ".tar": "application/x-tar",
    ".gz": "application/gzip",
    ".yaml": "application/x-yaml",
    ".yml": "application/x-yaml",
    ".toml": "application/toml",
    ".rst": "text/x-rst",
    ".org": "text/x-org",
    ".tex": "application/x-latex",
    ".bib": "application/x-bibtex",
    ".ipynb": "application/x-ipynb+json",
}


def mime_type_from_filename(filename: str) -> str | None:
    """Resolve MIME type from a filename extension.

    Returns None if the extension is not recognized.
    """
    from pathlib import PurePath

    ext = PurePath(filename).suffix.lower()
    return _EXTENSION_TO_MIME.get(ext)


class KreuzbergReader:
    """Extract text (as markdown) and metadata from files via kreuzberg."""

    def __init__(self, reader_options: dict[str, Any] | None = None):
        self._options = reader_options or {}

    async def extract_from_bytes(
        self,
        data: bytes,
        *,
        mime_type: str | None = None,
        filename: str | None = None,
    ) -> tuple[str, dict[str, Any]]:
        """Extract markdown content and metadata from raw bytes.

        Args:
            data: File content as bytes.
            mime_type: Explicit MIME type. If None, inferred from filename.
            filename: Original filename (used for MIME detection fallback).

        Returns:
            Tuple of (markdown_content, metadata_dict).

        Raises:
            ValueError: If MIME type cannot be determined.
        """
        resolved_mime = mime_type
        if not resolved_mime and filename:
            resolved_mime = mime_type_from_filename(filename)
        if not resolved_mime:
            # Let kreuzberg try to detect from bytes
            try:
                from kreuzberg import detect_mime_type

                resolved_mime = detect_mime_type(data)
            except Exception:
                pass
        if not resolved_mime:
            raise ValueError(
                "Cannot determine MIME type. Provide mime_type or filename."
            )

        config = ExtractionConfig(
            output_format="markdown",
            pages=PageConfig(
                extract_pages=True,
                insert_page_markers=True,
                marker_format="\n\n[Page: {page_num}]\n\n",
            ),
        )

        # Configure OCR if requested via reader options or env vars
        if self._options.get("ocr"):
            ocr_backend = self._options.get(
                "ocr_backend",
                os.environ.get("KREUZBERG_OCR_BACKEND", "tesseract"),
            )
            ocr_language = self._options.get(
                "ocr_language",
                os.environ.get("KREUZBERG_OCR_LANGUAGE", "eng"),
            )
            config.ocr = OcrConfig(
                backend=ocr_backend,
                language=ocr_language,
            )

        logger.info(
            "Extracting content via kreuzberg",
            extra={"mime_type": resolved_mime, "size": len(data)},
        )

        result: ExtractionResult = await extract_bytes(
            data, resolved_mime, config=config
        )

        metadata = self._build_metadata(result)

        logger.info(
            "Kreuzberg extraction complete",
            extra={
                "content_length": len(result.content),
                "page_count": metadata.get("total_pages"),
                "tables_count": metadata.get("tables_count", 0),
            },
        )

        return result.content, metadata

    def _build_metadata(self, result: ExtractionResult) -> dict[str, Any]:
        """Build a metadata dict from an ExtractionResult."""
        meta: dict[str, Any] = {}

        page_count = result.get_page_count()
        if page_count:
            meta["total_pages"] = page_count

        if result.metadata:
            for key in ("title", "authors", "subject", "keywords"):
                val = result.metadata.get(key)
                if val:
                    meta[key] = val
            format_type = result.metadata.get("format_type")
            if format_type:
                meta["format_type"] = format_type

        if result.tables:
            meta["tables_count"] = len(result.tables)

        if result.detected_languages:
            meta["detected_languages"] = result.detected_languages

        return meta
