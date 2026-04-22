from .chunkers import (
    DeterministicRecursiveChunker,
    HtmlLlmChunker,
    KreuzbergChunker,
    LLMChunker,
    NoneChunker,
)
from .models import ChunkerResult, ChunkerStrategy, ContentConfig


async def split_content(
    content: str,
    config: ContentConfig,
    *,
    document_title: str | None = None,
    source_url: str | None = None,
) -> ChunkerResult:
    strategy = config.chunker.get("strategy", "").lower() if config.chunker else ""

    match strategy:
        case ChunkerStrategy.NONE:
            chunker = NoneChunker(config)
        case ChunkerStrategy.LLM:
            chunker = LLMChunker(config)
        case ChunkerStrategy.RECURSIVE:
            chunker = DeterministicRecursiveChunker(config)
        case ChunkerStrategy.KREUZBERG:
            chunker = KreuzbergChunker(config)
        case ChunkerStrategy.HTML_LLM:
            chunker = HtmlLlmChunker(config)
        case _:
            raise ValueError(f"Unsupported strategy: {strategy!r}")

    result = await chunker.chunk_text(
        content, document_title=document_title, source_url=source_url
    )

    # Apply chunk_content_type from profile options to each chunk's content_format
    options = config.chunker.get("options", {}) if config.chunker else {}
    chunk_content_type = options.get("chunk_content_type") or None
    if chunk_content_type:
        for chunk in result.chunks:
            if not chunk.content_format:
                chunk.content_format = chunk_content_type

    return result
