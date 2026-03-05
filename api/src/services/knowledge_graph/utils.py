from __future__ import annotations

import logging
import re
from typing import Any

from .models import MetadataMultiValueContainer

logger = logging.getLogger(__name__)


def normalize_metadata_value(value: Any) -> Any:
    """Normalize metadata values for JSON storage.

    Converts MetadataMultiValueContainer (and other non-JSON containers) into
    JSON-friendly structures while preserving nested values.
    """
    if isinstance(value, MetadataMultiValueContainer):
        return [normalize_metadata_value(v) for v in value.values]
    if isinstance(value, dict):
        return {k: normalize_metadata_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [normalize_metadata_value(v) for v in value]
    return value


def convert_markdown_toc_to_json(markdown: str) -> list[dict[str, Any]]:
    """Convert a markdown TOC-like content into a JSON tree structure.

    Rules:
    - Only ATX headings (# .. ######) are treated as section delimiters.
    - Text lines are associated with the most recent heading at the current depth.
    - Nested headings create children of the nearest ancestor with a lower level.
    - Content before the first heading is ignored.

    Returns a list of root-level nodes, each with: { name, text, children }.
    """
    if not markdown:
        return []

    try:
        root: list[dict[str, Any]] = []
        stack: list[tuple[int, dict[str, Any]]] = []  # (level, node)
        in_fenced_block = False

        heading_re = re.compile(r"^(#{1,6})\s+(.*)$")
        fence_re = re.compile(r"^```+")

        for raw_line in markdown.splitlines():
            line = raw_line.rstrip("\n")

            # Toggle fenced code blocks to avoid parsing headings inside code
            if fence_re.match(line):
                in_fenced_block = not in_fenced_block
            if in_fenced_block:
                # Treat code as regular text if within a section
                if stack:
                    stack[-1][1].setdefault("text_lines", []).append(line)
                continue

            m = heading_re.match(line)
            if m:
                level = len(m.group(1))
                title = (
                    m.group(2).strip().rstrip("#").strip()
                )  # trim trailing #'s if present

                node: dict[str, Any] = {"name": title, "text_lines": [], "children": []}

                # Find parent by popping until the stack top has lower level
                while stack and stack[-1][0] >= level:
                    stack.pop()

                if stack:
                    stack[-1][1]["children"].append(node)
                else:
                    root.append(node)

                stack.append((level, node))
            else:
                # Regular text goes to the current section (last heading)
                if stack:
                    stack[-1][1].setdefault("text_lines", []).append(line)
                else:
                    # Ignore text before the first heading
                    continue

        def _finalize_nodes(nodes: list[dict[str, Any]]):
            for node in nodes:
                lines: list[str] = node.pop("text_lines", [])
                # Preserve intra-paragraph newlines but trim leading/trailing whitespace
                text = "\n".join(lines).strip()
                node["text"] = text
                children = node.get("children", []) or []
                if children:
                    _finalize_nodes(children)

        # Finalize text fields
        _finalize_nodes(root)
        return root
    except Exception as e:
        logger.error(f"Failed to convert markdown TOC to JSON: {e}")
        return []
