from .chunkers import DeterministicRecursiveChunker, LLMChunker, NoneChunker
from .models import ChunkerResult, ChunkerStrategy, ContentConfig


async def split_content(
    content: str, config: ContentConfig, *, document_title: str | None = None
) -> ChunkerResult:
    strategy = config.chunker.get("strategy", "").lower() if config.chunker else ""

    match strategy:
        case ChunkerStrategy.NONE:
            chunker = NoneChunker(config)
        case ChunkerStrategy.LLM:
            chunker = LLMChunker(config)
        case ChunkerStrategy.RECURSIVE:
            chunker = DeterministicRecursiveChunker(config)
        case _:
            raise ValueError(f"Unsupported strategy: {strategy!r}")

    return await chunker.chunk_text(content, document_title=document_title)
