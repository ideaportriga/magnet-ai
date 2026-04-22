import asyncio
import copy
import logging
import re
from typing import Any, override
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, NavigableString, Tag

from core.db.models.knowledge_graph import KnowledgeGraphChunk
from services.prompt_templates import execute_prompt_template

from ..models import ChunkerResult, ContentConfig, DocumentMetadata
from .abstract_chunker import AbstractChunker

logger = logging.getLogger(__name__)

# Inline/formatting tags that should NOT receive an `i` annotation.
# These are too granular to be useful as chunk containers.
DEFAULT_SKIP_TAGS: set[str] = {
    "strong",
    "b",
    "em",
    "i",
    "a",
    "br",
    "wbr",
    "sub",
    "sup",
    "mark",
    "small",
    "del",
    "ins",
    "code",
    "kbd",
    "samp",
    "var",
    "cite",
    "q",
    "dfn",
    "time",
    "data",
    "bdi",
    "bdo",
    "ruby",
    "rt",
    "rp",
    "abbr",
    "tbody",
    "thead",
    "tfoot",
    "caption",
}

# Tags whose content is not useful for structure analysis.
NON_CONTENT_TAGS: set[str] = {
    "script",
    "style",
    "noscript",
    "svg",
    "iframe",
    "canvas",
    "template",
    "head",
}

# Interactive/form controls — fully decomposed from the parsed soup.
INTERACTIVE_TAGS: set[str] = {
    "input",
    "select",
    "option",
    "optgroup",
    "datalist",
    "textarea",
    "button",
    "fieldset",
    "legend",
    "output",
    "progress",
    "meter",
}

# Inline formatting tags unwrapped in simplified HTML (markup dropped, text kept).
UNWRAP_TAGS: set[str] = {
    "a",
    "b",
    "strong",
    "i",
    "em",
    "u",
    "mark",
    "small",
    "sub",
    "sup",
    "code",
    "kbd",
    "samp",
    "var",
    "cite",
    "q",
    "dfn",
    "time",
    "data",
    "bdi",
    "bdo",
    "ruby",
    "rt",
    "rp",
    "abbr",
    "del",
    "ins",
    "wbr",
    "label",
}

# Tags preserved even when they have no text content (meaningful void elements).
EMPTY_PRESERVE_TAGS: set[str] = {"br", "hr", "img"}

DEFAULT_KEEP_ATTRIBUTES: set[str] = {
    "i",
    "id",
    "name",
    "alt",
    "colspan",
    "rowspan",
    "scope",
    "headers",
    "start",
    "type",
}

DEFAULT_TEXT_TRUNCATE_LENGTH = 100

# Accept both plain and markdown-bold forms:
# "TITLE: value", "**TITLE:** value", "**TITLE**: value"
_TITLE_LINE_RE = re.compile(
    r"^\*{0,2}\s*TITLE\s*\*{0,2}\s*:\*{0,2}\s*(.*)$", re.IGNORECASE
)
_IDS_LINE_RE = re.compile(r"^\*{0,2}\s*IDS\s*\*{0,2}\s*:\*{0,2}\s*(.*)$", re.IGNORECASE)


class HtmlLlmChunker(AbstractChunker):
    """Chunker that uses LLM to identify main content blocks in HTML.

    Pipeline:
    1. Parse HTML and extract content area
    2. Annotate significant tags with a sequential `i` attribute
    3. Simplify the annotated HTML (truncate text, strip attributes)
    4. Send simplified HTML to LLM to identify main block containers
    5. Extract each identified container from the original HTML as a chunk
    """

    def __init__(self, config: ContentConfig) -> None:
        super().__init__(config)
        self._options = config.chunker.get("options", {}) if config.chunker else {}
        # Populated for the duration of a single segmentation pass. Maps
        # id(tag) -> simplified HTML string. Lets us avoid re-simplifying the
        # same subtree when computing element sizes across the splittable /
        # element_sizes / per-segment steps.
        self._simplify_cache: dict[int, str] | None = None

    # ------------------------------------------------------------------
    # Configuration helpers
    # ------------------------------------------------------------------

    @property
    def _skip_tags(self) -> set[str]:
        custom = self._options.get("skip_tags")
        if custom and isinstance(custom, list):
            return set(custom)
        return DEFAULT_SKIP_TAGS

    @property
    def _keep_attributes(self) -> set[str]:
        custom = self._options.get("keep_attributes")
        if custom and isinstance(custom, list):
            return set(custom)
        return DEFAULT_KEEP_ATTRIBUTES

    @property
    def _text_truncate_length(self) -> int:
        return int(
            self._options.get("text_truncate_length", DEFAULT_TEXT_TRUNCATE_LENGTH)
        )

    @property
    def _segment_size(self) -> int:
        return int(self._options.get("llm_batch_size", 20000))

    @property
    def _llm_concurrency(self) -> int:
        return max(1, int(self._options.get("llm_concurrency", 4)))

    @property
    def _last_segment_increase_ratio(self) -> float:
        ratio = float(self._options.get("llm_last_segment_increase", 0.6))
        return max(0.0, min(1.0, ratio))

    @property
    def _content_selector(self) -> str | None:
        return self._options.get("content_selector") or None

    @property
    def _additional_instructions(self) -> str:
        return str(self._options.get("additional_instructions", ""))

    @property
    def _prompt_template_system_name(self) -> str:
        name = self._options.get("prompt_template_system_name", "")
        if not name:
            raise ValueError(
                "prompt_template_system_name is required for HTML LLM chunker"
            )
        return str(name)

    # ------------------------------------------------------------------
    # Step 1: Extract content area
    # ------------------------------------------------------------------

    def _extract_content_area(self, html: str) -> BeautifulSoup:
        """Parse HTML and scope to the main content area.

        Removes non-content tags (script, style, nav, footer, etc.).
        """
        soup = BeautifulSoup(html, "html.parser")

        # Remove non-content and interactive/form tags globally
        for tag_name in NON_CONTENT_TAGS | INTERACTIVE_TAGS:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        # If a CSS selector is configured, scope to matching elements
        if self._content_selector:
            elements = soup.select(self._content_selector)
            if elements:
                new_soup = BeautifulSoup("", "html.parser")
                wrapper = new_soup.new_tag("div")
                new_soup.append(wrapper)
                for el in elements:
                    wrapper.append(copy.copy(el))
                soup = new_soup

        # Remove nav/footer within content area
        for tag_name in ("nav", "footer", "header"):
            for tag in soup.find_all(tag_name):
                tag.decompose()

        return soup

    # ------------------------------------------------------------------
    # Step 1b: Collapse trivial wrappers
    # ------------------------------------------------------------------

    @staticmethod
    def _unwrap_trivial_wrappers(soup: BeautifulSoup) -> int:
        """Unwrap generic <div>/<span> wrappers that add no semantic value.

        Real-world HTML often contains chains like <div><div><div>…</div></div></div>
        where each level is a layout-only wrapper. Every one of them would otherwise
        receive an `i` annotation and consume LLM input tokens for no gain.

        A wrapper is considered trivial when ALL of the following hold:
          - The tag is <div> or <span>
          - It carries no attribute other than `class` / `style`
            (so `id`, `name`, `alt`, `role`, `aria-*`, `data-*`, etc. are preserved)
          - It has no direct text content (only whitespace)
          - It has exactly one element child

        Returns the number of wrappers unwrapped.
        """
        WRAPPER_TAGS: tuple[str, ...] = ("div", "span")
        ALLOWED_ATTRS: set[str] = {"class", "style"}

        def is_trivial(tag: Tag) -> bool:
            if tag.name not in WRAPPER_TAGS:
                return False
            # Any structural/semantic attribute disqualifies the tag.
            for attr in tag.attrs:
                if attr not in ALLOWED_ATTRS:
                    return False
            # Any non-whitespace direct text disqualifies the tag.
            element_children: list[Tag] = []
            for child in tag.children:
                if isinstance(child, NavigableString):
                    if child.strip():
                        return False
                elif isinstance(child, Tag):
                    element_children.append(child)
            return len(element_children) == 1

        total = 0
        # Snapshot the list up-front — we mutate the tree while iterating.
        # Unwrapping a trivial wrapper reparents its single child to the
        # wrapper's parent without changing the parent's element count, so
        # a single document-order pass handles nested chains correctly.
        for tag in list(soup.find_all(list(WRAPPER_TAGS))):
            if is_trivial(tag):
                tag.unwrap()
                total += 1
        return total

    # ------------------------------------------------------------------
    # Step 2: Annotate tags with `i`
    # ------------------------------------------------------------------

    def _annotate_html(self, soup: BeautifulSoup) -> dict[str, Tag]:
        """Add `i` attribute to significant tags.

        Returns a mapping {id: tag} for later extraction.
        """
        id_map: dict[str, Tag] = {}
        skip = self._skip_tags
        counter = 0

        for tag in soup.find_all(True):
            if tag.name in skip:
                continue
            counter += 1
            tag_id = str(counter)
            tag["i"] = tag_id
            id_map[tag_id] = tag

        return id_map

    @staticmethod
    def _strip_descendant_ids(tag: Tag, id_map: dict[str, Tag]) -> int:
        """Remove `i` from every descendant of `tag`. Returns count removed."""
        removed = 0
        for descendant in tag.find_all(True):
            tag_id = descendant.get("i")
            if tag_id is not None:
                del descendant["i"]
                id_map.pop(tag_id, None)
                removed += 1
        return removed

    def _optimize_list_table_ids(
        self, soup: BeautifulSoup, id_map: dict[str, Tag]
    ) -> int:
        """Drop redundant ids on descendants of self-contained lists/tables.

        When a <ul>/<ol>/<table> fits inside one LLM segment, the container is
        always identified as a single block. Per-item ids on <li>/<tr>/<td>
        only inflate the simplified HTML without enabling finer chunking. For
        tables that don't fit, per-row shrinkage is attempted instead.
        """
        segment_size = self._segment_size
        removed = 0

        def simplified_size(el: Tag) -> int:
            return len(self._simplify_html(BeautifulSoup(str(el), "html.parser")))

        # Document-order traversal: an outer fitting container strips nested
        # inner ones before they're visited (inner.get("i") is then None).
        for list_tag in soup.find_all(["ul", "ol"]):
            if list_tag.get("i") is None:
                continue
            if simplified_size(list_tag) <= segment_size:
                removed += self._strip_descendant_ids(list_tag, id_map)

        for table_tag in soup.find_all("table"):
            if table_tag.get("i") is None:
                continue
            if simplified_size(table_tag) <= segment_size:
                removed += self._strip_descendant_ids(table_tag, id_map)
                continue
            for tr in table_tag.find_all("tr"):
                if tr.get("i") is None:
                    continue
                if simplified_size(tr) <= segment_size:
                    removed += self._strip_descendant_ids(tr, id_map)

        return removed

    # ------------------------------------------------------------------
    # Step 3: Simplify HTML for LLM
    # ------------------------------------------------------------------

    def _simplified_size(self, tag: Tag) -> int:
        """Return the simplified-HTML character length for a subtree.

        When `self._simplify_cache` is active (set in `_identify_blocks_segmented`),
        the simplified string is memoized by `id(tag)`. This avoids re-simplifying
        the same subtree across `_get_splittable_children`, the element_sizes
        pre-computation, and any follow-up sizing queries.
        """
        cache = self._simplify_cache
        if cache is not None:
            cached = cache.get(id(tag))
            if cached is not None:
                return len(cached)
        simplified = self._simplify_html(BeautifulSoup(str(tag), "html.parser"))
        if cache is not None:
            cache[id(tag)] = simplified
        return len(simplified)

    def _simplify_html(self, soup: BeautifulSoup) -> str:
        """Create a lightweight HTML representation for LLM analysis.

        - Unwraps inline formatting tags (markup dropped, text preserved)
        - Removes configured attributes (style, class, etc.)
        - Truncates text nodes to configured max length
        - Prunes tags with no meaningful text content
        - Collapses whitespace between tags
        """
        simplified = copy.copy(soup)
        truncate_len = self._text_truncate_length
        keep_attrs = self._keep_attributes

        # Unwrap inline formatting tags so the LLM sees text only.
        # Must happen before text truncation so merged runs get measured together.
        for tag in simplified.find_all(list(UNWRAP_TAGS)):
            tag.unwrap()
        # Consolidate adjacent NavigableStrings produced by unwrapping.
        simplified.smooth()

        # Unwrap <span> elements whose content is text-only (no child tags).
        # Reverse order so nested text-only spans are unwrapped bottom-up:
        # after the inner span is unwrapped, its parent becomes text-only too.
        for tag in list(simplified.find_all("span"))[::-1]:
            if not tag.find(True):
                tag.unwrap()
        simplified.smooth()

        # Keep only whitelisted attributes; drop everything else
        for tag in simplified.find_all(True):
            for attr in list(tag.attrs):
                if attr not in keep_attrs:
                    del tag.attrs[attr]

        # Truncate text nodes
        for text_node in list(simplified.find_all(string=True)):
            if not isinstance(text_node, NavigableString):
                continue
            original = str(text_node)
            stripped = original.strip()
            if not stripped:
                # Remove whitespace-only text nodes
                text_node.replace_with("")
                continue
            if len(stripped) > truncate_len:
                truncated = stripped[:truncate_len] + "…"
                text_node.replace_with(truncated)

        # Prune tags with no meaningful text content (bottom-up).
        # Reverse order ensures children are processed before parents, so a parent
        # whose only children were empty becomes empty itself.
        for tag in list(simplified.find_all(True))[::-1]:
            if tag.name in EMPTY_PRESERVE_TAGS:
                continue
            if tag.get_text(strip=True):
                continue
            # Preserve wrappers whose only descendants are meaningful void tags.
            if any(d.name in EMPTY_PRESERVE_TAGS for d in tag.find_all(True)):
                continue
            tag.decompose()

        result = str(simplified)

        # Collapse multiple whitespace between tags
        result = re.sub(r">\s+<", "><", result)
        # Collapse runs of whitespace within text
        result = re.sub(r"\s{2,}", " ", result)
        # Strip quotes around `i` attribute integer values (i="12" -> i=12).
        # Safe in HTML5 since the value is digits-only.
        result = re.sub(r'(\s)i="(\d+)"', r"\1i=\2", result)

        return result.strip()

    # ------------------------------------------------------------------
    # Step 4: LLM block identification
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_response_lines(
        response_text: str,
    ) -> list[tuple[str, list[str]]]:
        """Parse TITLE/IDS line pairs from LLM response.

        Accepts both plain and markdown-bold wrapped keys, e.g.
        "TITLE: foo", "**TITLE:** foo", "**TITLE**: foo".

        Returns list of (title, [id, ...]) tuples.
        """
        blocks: list[tuple[str, list[str]]] = []
        current_title = ""

        for line in response_text.splitlines():
            line = line.strip()
            if not line:
                continue

            title_match = _TITLE_LINE_RE.match(line)
            if title_match:
                current_title = title_match.group(1).strip().rstrip("*").strip()
                continue

            ids_match = _IDS_LINE_RE.match(line)
            if ids_match:
                ids_part = ids_match.group(1).strip().rstrip("*").strip()
                if not ids_part:
                    continue
                ids = [uid.strip() for uid in ids_part.split(",") if uid.strip()]
                if ids:
                    blocks.append((current_title, ids))
                    current_title = ""

        return blocks

    async def _identify_blocks_via_llm(
        self, simplified_html: str
    ) -> list[tuple[str, list[str]]]:
        """Send simplified HTML to LLM and get back grouped id values.

        Returns a list of (title, id_group) tuples. Each group is a list of
        one or more id values that should be combined into a single chunk.
        """
        template_values: dict[str, Any] = {
            "additional_instructions": self._additional_instructions,
        }

        user_content = (
            "Analyze the following simplified HTML and identify the main "
            "content blocks. For each block, output a REASON line, a TITLE "
            "line, and an IDS line with id value(s).\n\n"
            f"```html\n{simplified_html}\n```"
        )

        result = await execute_prompt_template(
            system_name_or_config=self._prompt_template_system_name,
            template_values=template_values,
            template_additional_messages=[{"role": "user", "content": user_content}],
        )

        if not result.content:
            logger.warning("Empty LLM response for HTML block identification")
            return []

        response_text = result.content.strip()
        blocks = self._parse_response_lines(response_text)

        if not blocks:
            logger.error(
                "No IDS: lines found in LLM response: %s",
                response_text[:500],
            )

        return blocks

    # ------------------------------------------------------------------
    # Step 4b: Handle oversized HTML via segmentation
    # ------------------------------------------------------------------

    def _get_splittable_children(self, root: Tag, segment_size: int) -> list[Tag]:
        """Get a flat list of children suitable for segmentation.

        If a direct child's simplified size exceeds segment_size, recurse
        into its children instead. This ensures no single element sent to
        the LLM is larger than the segment limit.
        """
        result: list[Tag] = []
        children = [c for c in root.children if isinstance(c, Tag)]

        for child in children:
            if self._simplified_size(child) > segment_size:
                # This child is too large — try its children
                grandchildren = [gc for gc in child.children if isinstance(gc, Tag)]
                if grandchildren:
                    result.extend(self._get_splittable_children(child, segment_size))
                else:
                    # Leaf-level tag that is still too large; include as-is
                    result.append(child)
            else:
                result.append(child)

        return result

    def _build_segments(
        self,
        splittable: list[Tag],
        element_sizes: list[int],
        segment_size: int,
        overlap_ratio: float,
        last_segment_increase_ratio: float,
    ) -> list[list[int]]:
        """Build segment index lists with overlap.

        Each segment is a list of indices into `splittable`. Consecutive
        segments overlap: trailing elements of segment N are repeated at the
        start of segment N+1, giving the LLM context across boundaries.

        Returns list of index-lists, e.g. [[0,1,2,3], [2,3,4,5,6], [5,6,7,8]].
        """
        overlap_budget = int(segment_size * overlap_ratio)
        extended_size = int(segment_size * (1.0 + last_segment_increase_ratio))

        segments: list[list[int]] = []
        start = 0

        while start < len(splittable):
            # Build one segment starting at `start`
            indices: list[int] = []
            size = 0

            for i in range(start, len(splittable)):
                el_size = element_sizes[i]

                # Check if remaining content fits in an extended last segment
                remaining = sum(element_sizes[i:])
                if indices and (size + remaining) <= extended_size:
                    indices.extend(range(i, len(splittable)))
                    break

                if size + el_size > segment_size and indices:
                    break

                indices.append(i)
                size += el_size

            segments.append(indices)

            if not indices or indices[-1] == len(splittable) - 1:
                break  # Reached the end

            # Determine the start of the next segment: walk backwards from
            # the end of the current segment to include ~overlap_budget of
            # content at the beginning of the next segment.
            overlap_start = indices[-1] + 1
            overlap_acc = 0
            for j in range(len(indices) - 1, -1, -1):
                idx = indices[j]
                if overlap_acc + element_sizes[idx] > overlap_budget:
                    break
                overlap_acc += element_sizes[idx]
                overlap_start = idx

            # Ensure forward progress: next segment must advance past current start
            if overlap_start <= start:
                overlap_start = min(start + 1, len(splittable))

            start = overlap_start

        return segments

    @staticmethod
    def _deduplicate_groups(
        all_segment_results: list[list[tuple[str, list[str]]]],
        all_segment_indices: list[list[int]],
    ) -> list[tuple[str, list[str]]]:
        """Deduplicate block groups across overlapping segments.

        For IDs that appear in overlapping regions, prefer the assignment from
        the LATER segment since it has forward context the earlier one lacked.

        Strategy:
        1. Process segments in order.
        2. Track which IDs have been "claimed" by finalized groups.
        3. For each new segment's groups:
           - If a group's IDs are ALL already claimed → skip (duplicate).
           - If a group has SOME overlap with claimed IDs → the later segment
             has better context. Remove the overlapping IDs from the earlier
             group(s) and accept the new group in full.
           - If no overlap → accept as-is.
        """
        if len(all_segment_results) <= 1:
            return all_segment_results[0] if all_segment_results else []

        # Final list of accepted groups
        finalized: list[tuple[str, list[str]]] = []
        # Map from id -> index in finalized
        id_to_group_idx: dict[str, int] = {}

        for seg_groups in all_segment_results:
            for title, ids in seg_groups:
                if not ids:
                    continue

                # Check overlap with already-claimed IDs
                overlapping_ids = set(ids) & set(id_to_group_idx.keys())

                if overlapping_ids == set(ids):
                    # All IDs already claimed → pure duplicate, skip
                    continue

                if overlapping_ids:
                    # Partial overlap: later segment has better context for
                    # boundary elements. Remove overlapping IDs from earlier
                    # groups and accept this group.
                    groups_to_update: set[int] = set()
                    for oid in overlapping_ids:
                        if oid in id_to_group_idx:
                            groups_to_update.add(id_to_group_idx[oid])
                            del id_to_group_idx[oid]

                    for gidx in groups_to_update:
                        old_title, old_ids = finalized[gidx]
                        new_ids = [i for i in old_ids if i not in overlapping_ids]
                        finalized[gidx] = (old_title, new_ids)

                # Accept the new group
                group_idx = len(finalized)
                finalized.append((title, ids))
                for uid in ids:
                    id_to_group_idx[uid] = group_idx

        # Remove groups that became empty after ID removal
        return [(t, ids) for t, ids in finalized if ids]

    async def _identify_blocks_segmented(
        self, soup: BeautifulSoup, id_map: dict[str, Tag]
    ) -> list[tuple[str, list[str]]]:
        """Handle oversized HTML by splitting into overlapping segments.

        Uses llm_batch_size and llm_last_segment_increase to control segment
        sizing. Uses a fixed overlap ratio so boundary elements are seen by
        both the preceding and following segments. Deduplicates groups across
        segments, preferring the later segment's grouping for overlap IDs.
        """
        self._simplify_cache = {}
        try:
            simplified = self._simplify_html(soup)
            segment_size = self._segment_size

            if len(simplified) <= segment_size:
                return await self._identify_blocks_via_llm(simplified)

            logger.info(
                "Simplified HTML (%d chars) exceeds segment size (%d), splitting",
                len(simplified),
                segment_size,
            )

            # Find top-level content container
            content_root = (
                soup.find("main") or soup.find("article") or soup.find("body") or soup
            )

            # Flatten children so that no single element exceeds segment_size
            splittable = self._get_splittable_children(content_root, segment_size)

            # Pre-compute simplified size for each element (served from cache
            # when `_get_splittable_children` already sized this element).
            element_sizes: list[int] = [self._simplified_size(el) for el in splittable]

            # Build overlapping segments
            overlap_ratio = 0.2  # 20% overlap between segments
            segments = self._build_segments(
                splittable,
                element_sizes,
                segment_size,
                overlap_ratio,
                self._last_segment_increase_ratio,
            )

            logger.info(
                "Split into %d segments with %.0f%% overlap",
                len(segments),
                overlap_ratio * 100,
            )

            # Prepare simplified payload per segment up-front.
            segment_payloads: list[str] = []
            for seg_num, indices in enumerate(segments):
                segment_tags = [splittable[i] for i in indices]
                segment_html = "".join(str(t) for t in segment_tags)
                segment_soup = BeautifulSoup(segment_html, "html.parser")
                segment_simplified = self._simplify_html(segment_soup)
                logger.info(
                    "Prepared segment %d/%d for LLM (%d chars, elements %d-%d)",
                    seg_num + 1,
                    len(segments),
                    len(segment_simplified),
                    indices[0],
                    indices[-1],
                )
                segment_payloads.append(segment_simplified)

            # Fan out segment LLM calls concurrently, bounded by a semaphore.
            semaphore = asyncio.Semaphore(self._llm_concurrency)

            async def run_segment(
                payload: str,
            ) -> list[tuple[str, list[str]]]:
                async with semaphore:
                    return await self._identify_blocks_via_llm(payload)

            all_segment_results: list[list[tuple[str, list[str]]]] = list(
                await asyncio.gather(*(run_segment(p) for p in segment_payloads))
            )

            # Deduplicate across overlapping segments
            return self._deduplicate_groups(all_segment_results, segments)
        finally:
            self._simplify_cache = None

    # ------------------------------------------------------------------
    # Step 5: Extract chunks from identified blocks
    # ------------------------------------------------------------------

    @staticmethod
    def _clean_tag_for_output(tag: Tag) -> Tag:
        """Create a lightweight copy of a tag for chunk content.

        Strips noisy attributes — styling (style, class), sizing
        (width, height), the chunker's own ``i`` annotation, data-*,
        event handlers, etc. — while preserving structural tags and
        meaningful attributes (href, src, alt, id, colspan, rowspan,
        etc.).
        """
        KEEP_ATTRIBUTES: set[str] = {
            "href",
            "src",
            "alt",
            "title",
            "id",
            "name",
            "colspan",
            "rowspan",
            "scope",
            "headers",
            "target",
            "rel",
            "type",
            "value",
            "placeholder",
            "for",
            "aria-label",
            "aria-describedby",
            "role",
            "lang",
            "dir",
            "datetime",
        }

        tag_copy = copy.copy(tag)
        for t in tag_copy.find_all(True):
            attrs_to_remove = [attr for attr in t.attrs if attr not in KEEP_ATTRIBUTES]
            for attr in attrs_to_remove:
                del t.attrs[attr]

        # Clean the root tag itself
        attrs_to_remove = [
            attr for attr in tag_copy.attrs if attr not in KEEP_ATTRIBUTES
        ]
        for attr in attrs_to_remove:
            del tag_copy.attrs[attr]

        return tag_copy

    @staticmethod
    def _resolve_links_in_tag(tag: Tag, base_url: str | None) -> None:
        """Rewrite relative ``href``/``src`` values against ``base_url``.

        Mutates ``tag`` in place. No-op when ``base_url`` is falsy. Empty
        values and non-http schemes (``mailto:``, ``tel:``, ``javascript:``,
        ``data:``, ...) are left untouched.
        """
        # TODO: srcset not yet handled — not in the output keep-list today,
        # but add comma-list parsing here if it ever is.
        if not base_url:
            return

        elements: list[Tag] = [tag, *tag.find_all(True)]
        for element in elements:
            for attr in ("href", "src"):
                value = element.get(attr)
                if not isinstance(value, str):
                    continue
                stripped = value.strip()
                if not stripped:
                    continue
                scheme = urlparse(stripped).scheme
                if scheme and scheme not in ("http", "https"):
                    continue
                element[attr] = urljoin(base_url, stripped)

    @staticmethod
    def _is_descendant_of(tag: Tag, ancestor: Tag) -> bool:
        """Check if tag is a descendant of ancestor."""
        parent = tag.parent
        while parent is not None:
            if parent is ancestor:
                return True
            parent = parent.parent
        return False

    @classmethod
    def _remove_nested_tags(cls, tags: list[Tag]) -> list[Tag]:
        """Remove tags that are descendants of other tags in the list.

        Prevents duplicate content when a parent and its child are both
        included in the same group.
        """
        if len(tags) <= 1:
            return tags

        result: list[Tag] = []
        for tag in tags:
            is_nested = any(
                cls._is_descendant_of(tag, other) for other in tags if other is not tag
            )
            if not is_nested:
                result.append(tag)
        return result

    @classmethod
    def _remove_nested_groups(
        cls,
        block_groups: list[tuple[str, list[str]]],
        id_map: dict[str, Tag],
    ) -> list[tuple[str, list[str]]]:
        """Remove groups whose tags are entirely contained within another group's tags.

        If group A contains a parent tag and group B contains a child of that
        parent, group B is redundant and will be dropped.
        """
        if len(block_groups) <= 1:
            return block_groups

        # Resolve tags for each group
        resolved: list[tuple[int, list[Tag]]] = []
        for i, (_, ids) in enumerate(block_groups):
            tags = [id_map[bid] for bid in ids if bid in id_map]
            resolved.append((i, tags))

        drop_indices: set[int] = set()

        for i, tags_i in resolved:
            if not tags_i:
                continue
            for j, tags_j in resolved:
                if i == j or not tags_j or j in drop_indices:
                    continue
                # Check if every tag in group i is a descendant of some tag in group j
                all_nested = all(
                    any(cls._is_descendant_of(tag_i, tag_j) for tag_j in tags_j)
                    for tag_i in tags_i
                )
                if all_nested:
                    drop_indices.add(i)
                    break

        if drop_indices:
            logger.info(
                "Removed %d groups nested inside other groups", len(drop_indices)
            )

        return [
            block_groups[i] for i in range(len(block_groups)) if i not in drop_indices
        ]

    def _extract_chunks_from_groups(
        self,
        id_map: dict[str, Tag],
        block_groups: list[tuple[str, list[str]]],
        source_url: str | None = None,
    ) -> list[KnowledgeGraphChunk]:
        """Extract chunk content from original HTML using grouped id mappings.

        Each group may contain one or more id values. Multiple IDs in a
        group are combined into a single chunk (e.g. a heading + table that
        are siblings without a common parent).
        """
        chunks: list[KnowledgeGraphChunk] = []

        for llm_title, group in block_groups:
            # Resolve tags for all IDs in the group
            tags: list[Tag] = []
            for bid in group:
                tag = id_map.get(bid)
                if tag is None:
                    logger.warning("id %s not found in HTML map, skipping", bid)
                    continue
                tags.append(tag)

            if not tags:
                continue

            # Remove nested tags to prevent duplicate content
            tags = self._remove_nested_tags(tags)

            # Combine HTML content from all tags in the group
            html_parts: list[str] = []
            text_parts: list[str] = []
            for tag in tags:
                clean_tag = self._clean_tag_for_output(tag)
                self._resolve_links_in_tag(clean_tag, source_url)
                html_part = str(clean_tag).strip()
                if html_part:
                    html_parts.append(html_part)
                text_part = tag.get_text(separator="\n", strip=True)
                if text_part:
                    text_parts.append(text_part)

            html_content = "\n".join(html_parts)
            text_content = "\n".join(text_parts)

            if not html_content.strip() or not text_content.strip():
                continue

            # Use LLM-generated title; fall back to first heading in the group
            title = llm_title
            if not title:
                for tag in tags:
                    heading = tag.find(re.compile(r"^h[1-6]$"))
                    if heading:
                        title = heading.get_text(strip=True)
                        break

            chunk = KnowledgeGraphChunk(
                chunk_type="HTML_BLOCK",
                title=title,
                content=html_content,
                content_format="html",
                embedded_content=text_content,
            )
            chunks.append(chunk)

        return chunks

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    @override
    async def chunk_text(
        self,
        text: str,
        *,
        document_title: str | None = None,
        source_url: str | None = None,
    ) -> ChunkerResult:
        """Chunk HTML by using LLM to identify main content blocks.

        1. Parse HTML, extract content area
        2. Annotate tags with sequential `i` ids
        3. Simplify annotated HTML for LLM
        4. Send to LLM to identify block containers
        5. Extract each container as a chunk
        """
        if not text or not text.strip():
            raise ValueError("HTML LLM chunker received empty input")

        # Step 1: Extract content area
        soup = self._extract_content_area(text)

        # Step 1b: Collapse generic <div>/<span> wrappers that carry no
        # semantic meaning — reduces the number of `i` annotations and the
        # size of the simplified HTML sent to the LLM.
        unwrapped = self._unwrap_trivial_wrappers(soup)
        if unwrapped:
            logger.info("Unwrapped %d trivial wrapper elements", unwrapped)

        # Step 2: Annotate tags with `i`
        id_map = self._annotate_html(soup)

        if not id_map:
            raise ValueError("No annotatable HTML tags found in document")

        logger.info("Annotated %d tags with id", len(id_map))

        # Step 2b: Strip redundant ids on descendants of self-contained lists/tables
        stripped = self._optimize_list_table_ids(soup, id_map)
        if stripped:
            logger.info(
                "Stripped %d redundant ids from self-contained lists/tables",
                stripped,
            )

        # Steps 3+4: Simplify and identify blocks (handles segmentation)
        block_groups = await self._identify_blocks_segmented(soup, id_map)

        if not block_groups:
            raise RuntimeError("LLM identified no content blocks in document")

        logger.info("LLM identified %d content blocks", len(block_groups))

        # Remove groups that are entirely nested inside other groups
        block_groups = self._remove_nested_groups(block_groups, id_map)

        # Step 5: Extract chunks
        chunks = self._extract_chunks_from_groups(id_map, block_groups, source_url)

        if not chunks:
            raise RuntimeError(
                "No valid chunks could be extracted from identified blocks"
            )

        # Extract document metadata from HTML
        doc_title = document_title
        if not doc_title:
            title_tag = soup.find("title")
            if title_tag:
                doc_title = title_tag.get_text(strip=True)
            else:
                h1 = soup.find("h1")
                if h1:
                    doc_title = h1.get_text(strip=True)

        document_metadata = None
        if doc_title:
            document_metadata = DocumentMetadata(title=doc_title)

        logger.info(
            "HTML LLM chunker produced %d chunks from %d identified blocks",
            len(chunks),
            len(block_groups),
        )

        return ChunkerResult(chunks=chunks, document_metadata=document_metadata)
