import logging
from typing import Any

from liteparse import CLINotFoundError, LiteParse, ParseResult

logger = logging.getLogger(__name__)


class LiteParseReader:
    """Extract text and metadata from documents via LiteParse (Node.js-backed)."""

    def __init__(self, reader_options: dict[str, Any] | None = None):
        self._options = reader_options or {}
        self._parser = LiteParse()

    async def extract_from_bytes(
        self,
        data: bytes,
        *,
        filename: str | None = None,
    ) -> tuple[str, dict[str, Any]]:
        """Extract text with [Page: N] markers from raw bytes.

        Args:
            data: File content as bytes.
            filename: Original filename (for logging/diagnostics).

        Returns:
            Tuple of (text_with_page_markers, metadata_dict).

        Raises:
            RuntimeError: If the LiteParse CLI (Node.js) is not available.
        """
        ocr_enabled = self._options.get("ocr", False)
        max_pages = self._options.get("max_pages")

        logger.info(
            "Extracting content via LiteParse",
            extra={"doc_filename": filename, "size": len(data), "ocr": ocr_enabled},
        )

        parse_kwargs: dict[str, Any] = {"ocr_enabled": ocr_enabled}
        if max_pages is not None:
            parse_kwargs["max_pages"] = int(max_pages)

        try:
            result: ParseResult = await self._parser.parse_async(data, **parse_kwargs)
        except CLINotFoundError as exc:
            raise RuntimeError(
                "LiteParse CLI not found. Ensure Node.js 18+ is installed "
                "and the liteparse CLI is available on PATH "
                "(npm install -g @llamaindex/liteparse)."
            ) from exc

        text = self._build_text_with_page_markers(result)
        metadata = self._build_metadata(result)

        logger.info(
            "LiteParse extraction complete",
            extra={
                "content_length": len(text),
                "page_count": metadata.get("total_pages"),
            },
        )

        return text, metadata

    def _build_text_with_page_markers(self, result: ParseResult) -> str:
        """Build text with [Page: N] markers from ParseResult pages.

        Uses the same marker format as KreuzbergReader so downstream
        chunkers that look for ``[Page: N]`` patterns work identically.
        """
        if not result.pages:
            return result.text or ""

        parts: list[str] = []
        for page in result.pages:
            parts.append(f"\n\n[Page: {page.pageNum}]\n\n")
            parts.append(page.text or "")

        return "".join(parts).strip()

    def _build_metadata(self, result: ParseResult) -> dict[str, Any]:
        """Build metadata dict from ParseResult."""
        meta: dict[str, Any] = {}
        if result.num_pages is not None:
            meta["total_pages"] = result.num_pages
        return meta
