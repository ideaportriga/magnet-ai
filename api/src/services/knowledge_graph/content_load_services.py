from .models import ContentConfig, ContentReaderName, LoadedContent
from .readers.kreuzberg_reader import KreuzbergReader, mime_type_from_filename
from .readers.pdf_reader import DefaultPdfReader


def load_content_from_bytes(file_bytes: bytes, config: ContentConfig) -> LoadedContent:
    """Synchronous content loader (legacy readers only).

    For kreuzberg-based extraction use ``load_content_from_bytes_async``.
    """
    reader_name = config.reader.get("name", "").lower() if config.reader else ""

    match reader_name:
        case ContentReaderName.PDF:
            text, total_pages = DefaultPdfReader().extract_text_from_bytes(file_bytes)
            return {"text": text, "metadata": {"total_pages": total_pages}}
        case ContentReaderName.PLAIN_TEXT:
            text = file_bytes.decode("utf-8", errors="replace")
            return {"text": text, "metadata": {}}
        case ContentReaderName.KREUZBERG:
            raise ValueError(
                "Kreuzberg reader requires async. Use load_content_from_bytes_async()."
            )
        case _:
            raise ValueError(f"Unsupported reader: {reader_name!r}")


async def load_content_from_bytes_async(
    file_bytes: bytes,
    config: ContentConfig,
    *,
    filename: str | None = None,
) -> LoadedContent:
    """Async content loader with kreuzberg support.

    Falls back to synchronous readers for PDF/plain_text.
    """
    reader_name = config.reader.get("name", "").lower() if config.reader else ""

    if reader_name == ContentReaderName.KREUZBERG:
        options = config.reader.get("options", {}) if config.reader else {}
        reader = KreuzbergReader(reader_options=options)

        mime_type: str | None = options.get("mime_type")
        if not mime_type and filename:
            mime_type = mime_type_from_filename(filename)

        text, metadata = await reader.extract_from_bytes(
            file_bytes, mime_type=mime_type, filename=filename
        )
        return {"text": text, "metadata": metadata}

    # Delegate to synchronous loader for legacy readers
    return load_content_from_bytes(file_bytes, config)
