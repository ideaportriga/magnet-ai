import logging
import re
from dataclasses import dataclass, field
from typing import Any, Mapping
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, NavigableString, Tag

logger = logging.getLogger(__name__)

SECTION_MARKER_TEMPLATE = "[[SP_SECTION_{index}]]"
NON_CONTENT_TAGS = {
    "script",
    "style",
    "noscript",
    "svg",
    "path",
    "iframe",
    "canvas",
    "template",
}
BLOCK_TAGS = {
    "address",
    "article",
    "aside",
    "blockquote",
    "caption",
    "div",
    "figcaption",
    "figure",
    "footer",
    "form",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "li",
    "main",
    "nav",
    "ol",
    "p",
    "pre",
    "section",
    "table",
    "tbody",
    "td",
    "tfoot",
    "th",
    "thead",
    "tr",
    "ul",
}
HIDDEN_CLASS_HINTS = (
    "screen-reader",
    "sr-only",
    "visually-hidden",
    "hidden",
)
IMAGE_SOURCE_ATTRIBUTES = (
    "src",
    "data-src",
    "data-original-src",
    "data-imageurl",
    "data-sp-imageurl",
    "data-sp-src",
)
IMAGE_TEXT_ATTRIBUTES = (
    "alt",
    "title",
    "aria-label",
    "data-caption",
    "data-image-title",
    "data-sp-prop-name",
)
BACKGROUND_IMAGE_RE = re.compile(
    r"background-image\s*:\s*url\((?P<quote>['\"]?)(?P<url>[^)\"']+)(?P=quote)\)",
    flags=re.IGNORECASE,
)
WHITESPACE_RE = re.compile(r"\s+")


@dataclass
class _SectionAccumulator:
    lines: list[str] = field(default_factory=list)
    current_line: str = ""
    image_count: int = 0

    def append_text(self, text: str) -> None:
        normalized = WHITESPACE_RE.sub(" ", (text or "").replace("\u200b", " ")).strip()
        if not normalized:
            return

        if not self.current_line:
            self.current_line = normalized
            return

        separator = ""
        if self.current_line[-1] not in " ([{/" and normalized[0] not in ",.;:!?)]}%":
            separator = " "

        self.current_line = f"{self.current_line}{separator}{normalized}"

    def flush_line(self) -> None:
        line = self.current_line.strip()
        if line:
            self.lines.append(line)
        self.current_line = ""

    def append_block_line(self, text: str) -> None:
        self.flush_line()
        normalized = WHITESPACE_RE.sub(" ", (text or "").replace("\u200b", " ")).strip()
        if normalized:
            self.lines.append(normalized)

    def to_text(self) -> str:
        self.flush_line()
        return "\n".join(line for line in self.lines if line).strip()


class DefaultSharePointPageReader:
    """Extract plain text and image data from SharePoint page canvas controls."""

    def __init__(self, section_marker_template: str = SECTION_MARKER_TEMPLATE):
        self.section_marker_template = section_marker_template

    def extract_text_from_bytes(
        self,
        page_bytes: bytes,
        *,
        context: Mapping[str, Any] | None = None,
    ) -> tuple[str, dict[str, Any]]:
        html = page_bytes.decode("utf-8", errors="replace")
        return self.extract_text_from_html(html, context=context)

    def extract_text_from_html(
        self,
        html: str,
        *,
        context: Mapping[str, Any] | None = None,
    ) -> tuple[str, dict[str, Any]]:
        if not isinstance(html, str) or not html.strip():
            return "", {"section_count": 0, "canvas_control_count": 0, "image_count": 0}

        soup = BeautifulSoup(html, "html.parser")
        canvas_sections = list(soup.select("div[data-sp-canvascontrol]"))
        base_url = self._resolve_base_url(context)

        sections: list[Tag] = canvas_sections
        if not sections:
            fallback_root = soup.body if isinstance(soup.body, Tag) else soup
            if isinstance(fallback_root, Tag):
                sections = [fallback_root]

        section_blocks: list[str] = []
        nonempty_section_count = 0
        image_count = 0

        for section_index, section in enumerate(sections, start=1):
            section_text, section_image_count = self._extract_section_text(
                section, base_url=base_url
            )
            if not section_text:
                continue

            if section_blocks:
                section_blocks.append(
                    self.section_marker_template.format(index=section_index)
                )
            section_blocks.append(section_text)
            nonempty_section_count += 1
            image_count += section_image_count

        text = "\n\n".join(section_blocks).strip()
        metadata = {
            "section_count": nonempty_section_count,
            "canvas_control_count": len(canvas_sections),
            "image_count": image_count,
        }
        return text, metadata

    def _extract_section_text(self, section: Tag, *, base_url: str) -> tuple[str, int]:
        accumulator = _SectionAccumulator()
        self._walk_node(section, accumulator, base_url=base_url, is_root=True)
        return accumulator.to_text(), accumulator.image_count

    def _walk_node(
        self,
        node: Tag | NavigableString,
        accumulator: _SectionAccumulator,
        *,
        base_url: str,
        is_root: bool = False,
    ) -> None:
        if isinstance(node, NavigableString):
            accumulator.append_text(str(node))
            return

        if not isinstance(node, Tag):
            return

        if self._should_skip_tag(node):
            return

        tag_name = (node.name or "").lower()

        if tag_name == "br":
            accumulator.flush_line()
            return

        if tag_name == "img":
            self._append_image_line(node, accumulator, base_url=base_url)
            return

        if self._tag_represents_non_img_image(node):
            self._append_image_line(node, accumulator, base_url=base_url)

        is_block = tag_name in BLOCK_TAGS
        if is_block and not is_root:
            accumulator.flush_line()

        for child in node.children:
            self._walk_node(child, accumulator, base_url=base_url)

        if is_block:
            accumulator.flush_line()

    def _should_skip_tag(self, tag: Tag) -> bool:
        tag_name = (tag.name or "").lower()
        if tag_name in NON_CONTENT_TAGS:
            return True

        if tag.has_attr("hidden"):
            return True

        if str(tag.get("aria-hidden") or "").strip().lower() == "true" and not (
            tag.find("img") or self._tag_represents_non_img_image(tag)
        ):
            return True

        classes = " ".join(
            str(class_name).lower() for class_name in (tag.get("class") or [])
        )
        if classes and any(class_hint in classes for class_hint in HIDDEN_CLASS_HINTS):
            return True

        return False

    def _append_image_line(
        self,
        tag: Tag,
        accumulator: _SectionAccumulator,
        *,
        base_url: str,
    ) -> None:
        image_line = self._format_image_line(tag, base_url=base_url)
        if not image_line:
            return

        accumulator.append_block_line(image_line)
        accumulator.image_count += 1

    def _format_image_line(self, tag: Tag, *, base_url: str) -> str:
        raw_url = self._extract_image_url(tag)
        image_url = self._resolve_url(raw_url, base_url=base_url)
        description = self._extract_image_description(
            tag, fallback_url=image_url or raw_url
        )

        parts = ["Image:"]
        if description:
            parts.append(description)
        if image_url:
            parts.append(image_url)

        if len(parts) == 1:
            return ""
        return " ".join(parts)

    def _extract_image_url(self, tag: Tag) -> str:
        for attr_name in IMAGE_SOURCE_ATTRIBUTES:
            value = tag.get(attr_name)
            if isinstance(value, str) and value.strip():
                return value.strip()

        style = tag.get("style")
        if isinstance(style, str) and style.strip():
            match = BACKGROUND_IMAGE_RE.search(style)
            if match:
                return (match.group("url") or "").strip()

        return ""

    def _extract_image_description(self, tag: Tag, *, fallback_url: str) -> str:
        for attr_name in IMAGE_TEXT_ATTRIBUTES:
            value = tag.get(attr_name)
            if isinstance(value, str) and value.strip():
                return WHITESPACE_RE.sub(" ", value).strip()

        figcaption = tag.find_parent("figure")
        if isinstance(figcaption, Tag):
            caption = figcaption.find("figcaption")
            if isinstance(caption, Tag):
                caption_text = WHITESPACE_RE.sub(" ", caption.get_text(" ", strip=True))
                if caption_text:
                    return caption_text

        for ancestor in tag.parents:
            if not isinstance(ancestor, Tag):
                continue
            for attr_name in ("aria-label", "title", "data-caption"):
                value = ancestor.get(attr_name)
                if isinstance(value, str) and value.strip():
                    return WHITESPACE_RE.sub(" ", value).strip()

        fallback_name = self._extract_filename_from_url(fallback_url)
        return fallback_name

    def _resolve_base_url(self, context: Mapping[str, Any] | None) -> str:
        if not context:
            return ""

        for key in ("document_url", "site_url"):
            value = context.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

        return ""

    def _resolve_url(self, raw_url: str, *, base_url: str) -> str:
        value = str(raw_url or "").strip()
        if not value or value.startswith("data:"):
            return ""

        if not base_url:
            return value

        try:
            resolved = urljoin(base_url, value)
        except Exception:  # noqa: BLE001
            logger.debug("Failed to resolve SharePoint image URL", exc_info=True)
            return value

        parsed = urlparse(resolved)
        if parsed.scheme and parsed.netloc:
            return resolved
        return value

    def _extract_filename_from_url(self, value: str) -> str:
        parsed = urlparse(str(value or "").strip())
        path = parsed.path or str(value or "").strip()
        filename = path.rsplit("/", 1)[-1].strip()
        return filename

    def _tag_represents_non_img_image(self, tag: Tag) -> bool:
        tag_name = (tag.name or "").lower()
        if tag_name == "img":
            return False

        if self._extract_image_url(tag):
            return True

        role = str(tag.get("role") or "").strip().lower()
        if role == "img":
            return True

        return False
