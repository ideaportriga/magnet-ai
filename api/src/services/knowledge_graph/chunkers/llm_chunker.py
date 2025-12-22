import logging
import re
from typing import Any, override

from core.db.models.knowledge_graph import KnowledgeGraphChunk
from services.prompt_templates import execute_prompt_template

from ..models import ChunkerResult, ContentConfig, DocumentMetadata
from .abstract_chunker import AbstractChunker

logger = logging.getLogger(__name__)


class LLMChunker(AbstractChunker):
    def __init__(self, config: ContentConfig) -> None:
        super().__init__(config)

    @staticmethod
    def _strip_surrounding_code_fences(value: str) -> str:
        if not value:
            return value
        match = re.match(
            r"^\s*```[^\n]*\n([\s\S]*?)\n?\s*```\s*$", value, flags=re.DOTALL
        )
        return match.group(1).strip() if match else value

    def split_into_segments(self, text: str) -> list[str]:
        if not text:
            logger.warning("Empty text provided for segmenting")
            return []

        segments: list[str] = []
        text_length = len(text)

        # Get chunker options
        options = self.config.chunker.get("options", {})
        segment_size = int(options.get("llm_batch_size", 20000))
        segment_overlap_ratio = float(options.get("llm_batch_overlap", 0.1))
        segment_overlap_size = int(segment_size * segment_overlap_ratio)
        last_increase_ratio = float(options.get("llm_last_segment_increase", 0.6))
        last_increase_ratio = 0.0 if last_increase_ratio < 0 else last_increase_ratio
        last_increase_ratio = 1.0 if last_increase_ratio > 1 else last_increase_ratio

        # Calculate effective step size and initial start position
        step_size = max(segment_size - segment_overlap_size, 1)
        start_pos = 0

        while start_pos < text_length:
            # Calculate extended size for potential last segment merge
            extended_segment_size = int(segment_size * (1.0 + last_increase_ratio))

            # Check if remaining text fits within extended size (allows merge with previous)
            remaining = text_length - start_pos
            is_last = remaining <= extended_segment_size

            # End position: take all remaining if it fits extended size, otherwise normal segment
            if is_last:
                end_pos = text_length
            else:
                end_pos = min(start_pos + segment_size, text_length)

            # Extract segment
            segment = text[start_pos:end_pos]
            segments.append(segment)

            # If we've reached the end, break
            if end_pos >= text_length:
                break

            # Move to next segment with overlap
            start_pos += step_size

        logger.info(
            f"Split text of {text_length} chars into {len(segments)} segments "
            f"(size={segment_size}, overlap={segment_overlap_size})"
        )

        return segments

    @override
    async def chunk_text(self, text: str) -> ChunkerResult:
        # Get prompt template system name from config
        prompt_template_system_name = self.config.chunker.get("options", {}).get(
            "prompt_template_system_name"
        )
        if not prompt_template_system_name:
            raise ValueError(
                "Prompt template for LLM-based chunking is required and cannot be empty"
            )

        segments = self.split_into_segments(text)

        input_tokens = 0
        output_tokens = 0
        chunks: list[KnowledgeGraphChunk] = []
        # New document-level metadata extracted/updated across segments
        doc_title: str = ""
        doc_summary: str = ""
        doc_toc: str = ""

        prev_segment_input = ""
        prev_segment_output = ""

        for segment_index, segment in enumerate(segments):
            logger.info(
                f"Processing segment {segment_index + 1}/{len(segments)} ({len(segment)} chars)"
            )

            # Build template values for system prompt
            template_values = {}

            # Add previous segment output
            if segment_index > 0 and prev_segment_input:
                previous_segment_output = (
                    "**Previous Segment Output:**\n"
                    + "```\n"
                    + prev_segment_output
                    + "\n```"
                )
                template_values["previous_segment_output"] = previous_segment_output
            else:
                template_values["previous_segment_output"] = ""

            # Provide previous last-chunk hints to encourage partial-chunk repair
            template_values["previous_last_chunk_header"] = ""
            template_values["previous_last_chunk_content_tail"] = ""
            if segment_index > 0 and prev_segment_output:
                try:
                    prev_chunks_list = [
                        c.strip()
                        for c in prev_segment_output.split("<|SPLIT|>")
                        if c and c.strip()
                    ]
                    if prev_chunks_list:
                        prev_last_chunk_full = prev_chunks_list[-1]
                        prev_last_header_match = re.match(
                            r"^\(chunk<\|>.*\)$",
                            prev_last_chunk_full,
                            flags=re.MULTILINE,
                        )
                        prev_last_header = (
                            prev_last_header_match.group(0)
                            if prev_last_header_match
                            else ""
                        )
                        prev_last_body = prev_last_chunk_full.removeprefix(
                            prev_last_header
                        ).strip()
                        template_values["previous_last_chunk_header"] = prev_last_header
                        tail_len = 500
                        if prev_last_body:
                            template_values["previous_last_chunk_content_tail"] = (
                                prev_last_body[-tail_len:]
                                if len(prev_last_body) > tail_len
                                else prev_last_body
                            )
                except Exception as e:
                    logger.warning(
                        f"Failed to extract previous last chunk hints for repair: {e}"
                    )

            # Add current document state if processing multiple segments
            if len(segments) > 1 and segment_index > 0:
                current_state = (
                    "**Current Document State (accumulated so far):**\n\n"
                    + "Summary:\n"
                    + (doc_summary or "(not yet extracted)")
                    + "\n\n"
                    + "Table of Contents:\n"
                    + (doc_toc or "(not yet extracted)")
                )
                template_values["current_state"] = current_state
            else:
                template_values["current_state"] = ""

            # Simple user message with just the input text
            user_content = f"Process the following input text:\n\n```\n{segment}\n```"

            # Call prompt template for chunking
            try:
                result = await execute_prompt_template(
                    system_name_or_config=prompt_template_system_name,
                    template_values=template_values,
                    template_additional_messages=[
                        {"role": "user", "content": user_content}
                    ],
                )

                unprocessed_data = result.content
                if not unprocessed_data:
                    logger.warning(f"Empty response for segment {segment_index + 1}")
                    continue

                unprocessed_data = unprocessed_data.strip()

                # Strip surrounding code fences if present (e.g., ```json ... ```)
                unprocessed_data = self._strip_surrounding_code_fences(unprocessed_data)

                # Track tokens
                if result.usage:
                    input_tokens += int(result.usage.get("prompt_tokens", 0))
                    output_tokens += int(result.usage.get("completion_tokens", 0))

                if "<|DOCUMENT|>" not in unprocessed_data:
                    logger.warning(
                        f"Missing <|DOCUMENT|> marker in response for segment {segment_index + 1}"
                    )
                    continue

                if "<|CHUNKS|>" not in unprocessed_data:
                    logger.warning(
                        f"Missing <|CHUNKS|> marker in response for segment {segment_index + 1}"
                    )
                    continue

                if "<|COMPLETED|>" not in unprocessed_data:
                    logger.warning(
                        f"Missing <|COMPLETED|> marker in response for segment {segment_index + 1}"
                    )
                    continue

                # Remove completion marker
                unprocessed_data = unprocessed_data.removesuffix(
                    "<|COMPLETED|>"
                ).strip()

                # Extract/refresh document-level metadata whenever provided
                try:
                    chunks_marker_idx = unprocessed_data.find("<|CHUNKS|>")
                    meta_block = (
                        unprocessed_data[:chunks_marker_idx]
                        if chunks_marker_idx != -1
                        else unprocessed_data
                    )
                    # Parse tags
                    title_match = re.search(r"<TITLE>([\s\S]*?)</TITLE>", meta_block)
                    summary_match = re.search(
                        r"<SUMMARY>([\s\S]*?)</SUMMARY>", meta_block
                    )
                    toc_match = re.search(r"<TOC>([\s\S]*?)</TOC>", meta_block)
                    if title_match and not doc_title:
                        doc_title = title_match.group(1).strip()
                    if summary_match:
                        doc_summary = summary_match.group(1).strip()
                    if toc_match:
                        doc_toc = toc_match.group(1).strip()
                    # Reduce unprocessed_data to just the chunks portion if marker exists
                    if chunks_marker_idx != -1:
                        unprocessed_data = unprocessed_data[
                            chunks_marker_idx + len("<|CHUNKS|>") :
                        ].strip()
                except Exception as e:
                    logger.warning(f"Failed to parse document metadata: {e}")

                if len(unprocessed_data) == 0:
                    logger.info(
                        f"Skipped empty segment {segment_index + 1}/{len(segments)}"
                    )
                    continue

                if unprocessed_data.startswith("<|CHUNKS|>"):
                    unprocessed_data = unprocessed_data[len("<|CHUNKS|>") :].strip()

                # Split into individual chunks
                raw_segment_chunks = unprocessed_data.split("<|SPLIT|>")

                # Process each chunk
                curr_segment_chunks: list[KnowledgeGraphChunk] = []
                for chunk_str in raw_segment_chunks:
                    chunk_str = chunk_str.strip()

                    # Extract chunk header (chunk<|>type<|>title<|>toc_reference<|>page)
                    chunk_header_match = re.match(
                        r"^\(chunk<\|>.*\)$", chunk_str, flags=re.MULTILINE
                    )
                    chunk_header_str = (
                        chunk_header_match.group(0) if chunk_header_match else ""
                    )
                    chunk_str = chunk_str.removeprefix(chunk_header_str).strip()

                    # Parse header components
                    chunk_header = (
                        chunk_header_str.removeprefix("(")
                        .removesuffix(")")
                        .strip()
                        .split("<|>")
                    )

                    # Extract chunk page number (try to parse from text if not in header)
                    page_num = -1
                    if len(chunk_header) > 4 and chunk_header[4]:
                        try:
                            page_num = int(chunk_header[4])
                        except (ValueError, IndexError):
                            pass

                    # Try to extract page from [Page: X] markers in text
                    if page_num == -1:
                        page_match = re.search(r"\[Page:\s*(\d+)\]", chunk_str)
                        if page_match:
                            try:
                                page_num = int(page_match.group(1))
                            except ValueError:
                                pass

                    # Apply optional title pattern
                    options = self.config.chunker.get("options", {})
                    pattern = options.get("chunk_title_pattern") or ""

                    def format_pattern(pat: str, values: dict[str, Any]) -> str:
                        return re.sub(
                            r"\{(\w+)\}", lambda m: str(values.get(m.group(1), "")), pat
                        )

                    computed_title = (
                        format_pattern(
                            pattern,
                            {
                                "index": len(chunks) + 1,
                                "page": page_num,
                                "type": (
                                    chunk_header[1] if len(chunk_header) > 1 else ""
                                ),
                                "toc_reference": (
                                    chunk_header[3] if len(chunk_header) > 3 else ""
                                ),
                                "llm_title": (
                                    chunk_header[2] if len(chunk_header) > 2 else ""
                                ),
                            },
                        )
                        if pattern
                        else (chunk_header[2] if len(chunk_header) > 2 else "")
                    )

                    chunk = KnowledgeGraphChunk(
                        generated_id=chunk_header_str,
                        chunk_type=chunk_header[1] if len(chunk_header) > 1 else "TEXT",
                        title=computed_title,
                        toc_reference=chunk_header[3] if len(chunk_header) > 3 else "",
                        page=page_num if page_num and page_num > 0 else None,
                        content=chunk_str,
                        embedded_content=chunk_str,
                    )

                    # Check for duplicates
                    is_duplicate = False
                    for i, existing in enumerate(chunks):
                        if existing.generated_id == chunk.generated_id:
                            # Prefer replacement when:
                            # - It is the last chunk from a previous segment, OR
                            # - The new chunk contains more content (likely a repaired/extended version)
                            new_len = len(chunk.content or "")
                            old_len = len(existing.content or "")
                            if i == len(chunks) - 1 or new_len > old_len:
                                logger.info(
                                    f"Replacing duplicate chunk with updated content: {chunk.generated_id}"
                                )
                                chunks[i] = chunk
                                curr_segment_chunks.append(chunk)
                            else:
                                logger.warning(
                                    f"Skipping duplicate chunk (no improvement): {chunk.generated_id}"
                                )
                            is_duplicate = True
                            break

                    if is_duplicate:
                        continue

                    curr_segment_chunks.append(chunk)
                    chunks.append(chunk)

                # Store for next iteration
                prev_segment_input = segment
                prev_segment_output = unprocessed_data

                logger.info(
                    f"Segment {segment_index + 1}/{len(segments)} generated {len(curr_segment_chunks)} chunks"
                )

            except Exception as e:  # noqa: BLE001 - continue with next segment
                logger.error(
                    f"Error processing segment {segment_index + 1}/{len(segments)}: {e}",
                    exc_info=True,
                )
                # Continue with next segment, but this is a problem we should track
                continue

        logger.info(
            f"Processed {len(segments)} segments into {len(chunks)} chunks. "
            f"Tokens: {input_tokens} input, {output_tokens} output"
        )

        # Build document metadata if any was extracted
        document_metadata = None
        if doc_title or doc_summary or doc_toc:
            document_metadata = DocumentMetadata(
                title=doc_title if doc_title else None,
                summary=doc_summary if doc_summary else None,
                toc=doc_toc if doc_toc else None,
            )

        return ChunkerResult(chunks=chunks, document_metadata=document_metadata)
