"""Format tool payloads as markdown for the LLM agent messages."""

import json
from typing import Any

from .image_utils import strip_images


def format_tool_payload(
    tool_name: str,
    payload: dict[str, Any],
    image_registry: dict[str, str] | None = None,
) -> str:
    """Convert a structured tool payload into a readable markdown string.

    Parameters
    ----------
    tool_name:
        The name of the tool that produced the payload.
    payload:
        The structured payload returned by the tool.
    image_registry:
        Optional dict to collect stripped image mappings (uuid -> original html).
        Only used for ``findChunksBySimilarity``.
    """
    if tool_name == "findChunksBySimilarity":
        return _format_chunks(payload, image_registry)
    if tool_name == "findDocumentsByMetadata":
        return _format_matched_documents(payload, "Metadata Filter Results")
    if tool_name == "findDocumentsBySummarySimilarity":
        return _format_matched_documents(payload, "Document Search Results")
    if tool_name == "exit":
        return "Answer recorded."
    # Unknown tool – fall back to JSON
    return json.dumps(payload, ensure_ascii=False, default=str)


def _format_matched_documents(payload: dict[str, Any], heading: str) -> str:
    count = payload.get("matched_documents", 0)
    return f"## {heading}\nMatched documents: {count}"


def _format_chunks(
    payload: dict[str, Any],
    image_registry: dict[str, str] | None,
) -> str:
    chunks: list[dict[str, Any]] = payload.get("chunks") or []
    if not chunks:
        return "## Chunk Search Results\nNo chunks found."

    parts: list[str] = [f"## Chunk Search Results\nFound {len(chunks)} chunk(s).\n"]

    for i, chunk in enumerate(chunks, 1):
        section = _format_single_chunk(chunk, i, image_registry)
        parts.append(section)

    return "\n".join(parts)


def _format_single_chunk(
    chunk: dict[str, Any],
    index: int,
    image_registry: dict[str, str] | None,
) -> str:
    lines: list[str] = [f"---\n### Chunk {index}"]

    # Document info
    doc = chunk.get("document") or {}
    doc_title = doc.get("title") or doc.get("name")
    doc_name = doc.get("name")
    external_link = doc.get("external_link")
    if doc_title:
        doc_label = doc_title
        if doc_name and doc_name != doc_title:
            doc_label += f" ({doc_name})"
        if external_link:
            doc_label += f" | [link]({external_link})"
        lines.append(f"- **Document:** {doc_label}")

    # Chunk title
    chunk_title = chunk.get("title")
    if chunk_title:
        lines.append(f"- **Title:** {chunk_title}")

    # Page and section
    meta_parts: list[str] = []
    page = chunk.get("page")
    if page is not None:
        meta_parts.append(f"**Page:** {page}")
    toc_ref = chunk.get("toc_reference")
    if toc_ref:
        meta_parts.append(f"**Section:** {toc_ref}")
    if meta_parts:
        lines.append(f"- {' | '.join(meta_parts)}")

    # Score
    score = chunk.get("score")
    if score is not None:
        lines.append(f"- **Score:** {score:.2f}")

    # Content
    content = chunk.get("content") or ""
    if content:
        if image_registry is not None:
            content = strip_images(content, image_registry)
        lines.append(f"\n**Content:**\n{content}")

    return "\n".join(lines)
