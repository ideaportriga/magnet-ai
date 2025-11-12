from __future__ import annotations

import re
from typing import Callable

__all__ = ["to_slack_mrkdwn", "to_whatsapp_markdown"]

_BOLD_PATTERN = re.compile(r"\*\*([^*\n]+)\*\*")


def _normalize_bold(value: str) -> str:
    return _BOLD_PATTERN.sub(r"*\1*", value)


def _rewrite_links(markdown: str, format_link: Callable[[str, str], str]) -> str:
    if "[" not in markdown:
        return markdown

    result: list[str] = []
    index = 0
    length = len(markdown)

    while index < length:
        start = markdown.find("[", index)
        if start == -1:
            result.append(markdown[index:])
            break

        close_label = markdown.find("](", start)
        if close_label == -1:
            result.append(markdown[index:])
            break

        label = markdown[start + 1 : close_label]
        url_start = close_label + 2
        pos = url_start
        depth = 1

        while pos < length and depth > 0:
            char = markdown[pos]
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    break
            pos += 1

        if depth != 0:
            result.append(markdown[index:])
            break

        url = markdown[url_start:pos]
        formatted = format_link(label.strip(), url.strip())
        if not formatted:
            formatted = markdown[start : pos + 1]
        result.append(markdown[index:start])
        result.append(formatted)
        index = pos + 1

    return "".join(result)


def _convert_markdown(value: str | None, format_link: Callable[[str, str], str]) -> str:
    if not value:
        return ""

    normalized = value.replace("\r", "")
    normalized = _normalize_bold(normalized)
    return _rewrite_links(normalized, format_link)


def _escape_slack_link_text(text: str) -> str:
    return text.replace("|", r"\|")


def _escape_slack_link_url(url: str) -> str:
    replacements = {
        " ": "%20",
        "<": "%3C",
        ">": "%3E",
        "|": "%7C",
    }
    for char, replacement in replacements.items():
        url = url.replace(char, replacement)
    return url


def _format_slack_link(label: str, url: str) -> str:
    safe_label = _escape_slack_link_text(label) if label else ""
    safe_url = _escape_slack_link_url(url) if url else ""
    if safe_label and safe_url:
        return f"<{safe_url}|{safe_label}>"
    if safe_url:
        return f"<{safe_url}>"
    return safe_label


def to_slack_mrkdwn(value: str | None) -> str:
    return _convert_markdown(value, _format_slack_link)


def _format_whatsapp_link(label: str, url: str) -> str:
    if label and url:
        return f"{label} ({url})"
    return label or url


def to_whatsapp_markdown(value: str | None) -> str:
    return _convert_markdown(value, _format_whatsapp_link)

