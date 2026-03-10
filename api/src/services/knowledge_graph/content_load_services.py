from .models import (
    ContentConfig,
    ContentReaderContext,
    ContentReaderName,
    LoadedContent,
)
from .readers import DefaultPdfReader, DefaultSharePointPageReader


def load_content_from_bytes(
    file_bytes: bytes,
    config: ContentConfig,
    context: ContentReaderContext | None = None,
) -> LoadedContent:
    reader_name = config.reader.get("name", "").lower() if config.reader else ""

    match reader_name:
        case ContentReaderName.PDF:
            text, total_pages = DefaultPdfReader().extract_text_from_bytes(file_bytes)
            return {"text": text, "metadata": {"total_pages": total_pages}}
        case ContentReaderName.PLAIN_TEXT:
            text = file_bytes.decode("utf-8", errors="replace")
            return {"text": text, "metadata": {}}
        case ContentReaderName.SHAREPOINT_PAGE:
            text, metadata = DefaultSharePointPageReader().extract_text_from_bytes(
                file_bytes, context=context
            )
            return {"text": text, "metadata": metadata}
        case _:
            raise ValueError(f"Unsupported reader: {reader_name!r}")
