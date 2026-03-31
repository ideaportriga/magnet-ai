from .models import (
    ContentConfig,
    ContentReaderContext,
    ContentReaderName,
    LoadedContent,
)
from .readers import DefaultPdfReader, DefaultSharePointPageReader
from .readers.kreuzberg_reader import KreuzbergReader, mime_type_from_filename
from .readers.liteparse_reader import LiteParseReader


def load_content_from_bytes(
    file_bytes: bytes,
    config: ContentConfig,
    context: ContentReaderContext | None = None,
) -> LoadedContent:
    """Synchronous content loader (legacy readers only).

    For kreuzberg-based extraction use ``load_content_from_bytes_async``.
    """
    reader_name = config.reader.get("name", "").lower() if config.reader else ""

    match reader_name:
        case ContentReaderName.PDF:
            raw_text, text, total_pages = DefaultPdfReader().extract_text_from_bytes(
                file_bytes
            )
            return {
                "raw_text": raw_text,
                "text": text,
                "metadata": {"total_pages": total_pages},
            }
        case ContentReaderName.PLAIN_TEXT:
            text = file_bytes.decode("utf-8", errors="replace")
            return {"raw_text": text, "text": text, "metadata": {}}
        case ContentReaderName.KREUZBERG:
            raise ValueError(
                "Kreuzberg reader requires async. Use load_content_from_bytes_async()."
            )
        case ContentReaderName.LITEPARSE:
            raise ValueError(
                "LiteParse reader requires async. Use load_content_from_bytes_async()."
            )
        case ContentReaderName.SHAREPOINT_PAGE:
            raw_text, text, metadata = (
                DefaultSharePointPageReader().extract_text_from_bytes(
                    file_bytes, context=context
                )
            )
            return {"raw_text": raw_text, "text": text, "metadata": metadata}
        case _:
            raise ValueError(f"Unsupported reader: {reader_name!r}")


async def load_content_from_bytes_async(
    file_bytes: bytes,
    config: ContentConfig,
    *,
    filename: str | None = None,
    context: ContentReaderContext | None = None,
) -> LoadedContent:
    """Async content loader with kreuzberg support.

    Falls back to synchronous readers for PDF/plain_text/sharepoint_page.
    """
    reader_name = config.reader.get("name", "").lower() if config.reader else ""

    if reader_name == ContentReaderName.LITEPARSE:
        options = config.reader.get("options", {}) if config.reader else {}
        reader = LiteParseReader(reader_options=options)
        text, metadata = await reader.extract_from_bytes(file_bytes, filename=filename)
        return {"raw_text": text, "text": text, "metadata": metadata}

    if reader_name == ContentReaderName.KREUZBERG:
        options = config.reader.get("options", {}) if config.reader else {}
        reader = KreuzbergReader(reader_options=options)

        mime_type: str | None = options.get("mime_type")
        if not mime_type and filename:
            mime_type = mime_type_from_filename(filename)

        text, metadata = await reader.extract_from_bytes(
            file_bytes, mime_type=mime_type, filename=filename
        )
        return {"raw_text": text, "text": text, "metadata": metadata}

    # Delegate to synchronous loader for legacy readers
    return load_content_from_bytes(file_bytes, config, context=context)
