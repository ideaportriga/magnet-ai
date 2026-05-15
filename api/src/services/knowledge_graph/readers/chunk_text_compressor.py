"""Aggressively compress chunk text before sending it to an LLM for skip
detection -- i.e. deciding whether the chunk is worth running full entity
extraction on.

Design goals (priority order):
  1. Drop everything that doesn't carry signal about whether entities exist.
  2. Preserve entity hints: capitalization, numbers, currency, @ signs.
  3. Compress aggressively -- fewer tokens = cheaper skip checks.
  4. Never throw on weird PDF junk; degrade gracefully.

Python port of clean_example.js. Pure function, no I/O.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

DEFAULT_MAX_CHARS = 1500
DEFAULT_MIN_LINE_LENGTH = 3


@dataclass(slots=True, frozen=True)
class CompressionOptions:
    max_chars: int = DEFAULT_MAX_CHARS
    min_line_length: int = DEFAULT_MIN_LINE_LENGTH
    replace_urls: bool = True
    replace_emails: bool = True
    drop_pure_number_lines: bool = True


# Control characters PDFs love to embed (but keep \n=U+000A and \t=U+0009).
_CONTROL_CHARS_RE = re.compile("[\u0000-\u0008\u000b-\u001f\u007f-\u009f]")
_SMART_SINGLE_QUOTES_RE = re.compile("[‘’‚‛]")
_SMART_DOUBLE_QUOTES_RE = re.compile("[“”„‟]")
_EN_EM_DASH_RE = re.compile("[–—―]")
_ELLIPSIS_RE = re.compile("…")
_HYPHENATION_RE = re.compile(r"(\w)-\n([a-z])")
_URL_RE = re.compile(r"\bhttps?://\S+", re.IGNORECASE)
_EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b", re.IGNORECASE)
_DOT_LEADERS_RE = re.compile("[.·•‧]{3,}")
_RULE_LINES_RE = re.compile(r"[-=_*~^]{3,}")
_BOX_DRAWING_RE = re.compile("[─-╿]+")
_COLLAPSE_PUNCT_RE = re.compile(r"([!?,;:])\1+")
_CRLF_RE = re.compile(r"\r\n?")
_TAB_FF_VT_RE = re.compile(r"[\t\f\v]+")
_NBSP_RE = re.compile(" ")
_MULTI_SPACE_RE = re.compile(r" {2,}")
_SPACE_AROUND_NL_RE = re.compile(r" *\n *")
_MULTI_NL_RE = re.compile(r"\n{3,}")
_PAGE_NUM_RE = re.compile(r"^(?:page\s+)?\d{1,4}(?:\s*/\s*\d{1,4})?$", re.IGNORECASE)
_ROMAN_NUM_RE = re.compile(r"^[ivxlcdm]{1,6}$", re.IGNORECASE)
_HAS_LETTER_RE = re.compile(r"[A-Za-z]")
_NON_ALPHA_RE = re.compile(r"[^A-Za-z0-9\s]")
_PURE_NUMERIC_RE = re.compile(r"^[\d.,\s/-]+$")


def _normalize_unicode(s: str) -> str:
    try:
        return unicodedata.normalize("NFKC", s)
    except Exception:
        return s


def _strip_control_chars(s: str) -> str:
    return _CONTROL_CHARS_RE.sub("", s)


def _asciify_punctuation(s: str) -> str:
    s = _SMART_SINGLE_QUOTES_RE.sub("'", s)
    s = _SMART_DOUBLE_QUOTES_RE.sub('"', s)
    s = _EN_EM_DASH_RE.sub("-", s)
    s = _ELLIPSIS_RE.sub("...", s)
    return s


def _rejoin_hyphenation(s: str) -> str:
    # "exam-\nple" -> "example"; only join when next line starts lowercase,
    # so real compounds like "U.S.-\nbased" stay intact.
    return _HYPHENATION_RE.sub(r"\1\2", s)


def _mask_urls(s: str) -> str:
    return _URL_RE.sub("<URL>", s)


def _mask_emails(s: str) -> str:
    return _EMAIL_RE.sub("<EMAIL>", s)


def _strip_decorative(s: str) -> str:
    s = _DOT_LEADERS_RE.sub(" ", s)
    s = _RULE_LINES_RE.sub(" ", s)
    s = _BOX_DRAWING_RE.sub(" ", s)
    return s


def _collapse_punctuation(s: str) -> str:
    return _COLLAPSE_PUNCT_RE.sub(r"\1", s)


def _normalize_whitespace(s: str) -> str:
    s = _CRLF_RE.sub("\n", s)
    s = _TAB_FF_VT_RE.sub(" ", s)
    s = _NBSP_RE.sub(" ", s)
    s = _MULTI_SPACE_RE.sub(" ", s)
    s = _SPACE_AROUND_NL_RE.sub("\n", s)
    s = _MULTI_NL_RE.sub("\n\n", s)
    return s


def _is_junk_line(line: str, opts: CompressionOptions) -> bool:
    t = line.strip()
    if not t:
        return True
    if len(t) < opts.min_line_length:
        return True
    if _PAGE_NUM_RE.match(t):
        return True
    if _ROMAN_NUM_RE.match(t) and len(t) < 6:
        return True

    if not _HAS_LETTER_RE.search(t) and len(t) < 8:
        return True

    non_alpha = len(_NON_ALPHA_RE.findall(t))
    if non_alpha / len(t) > 0.7:
        return True

    if opts.drop_pure_number_lines and _PURE_NUMERIC_RE.match(t) and len(t) < 20:
        return True

    return False


def _filter_lines(s: str, opts: CompressionOptions) -> str:
    return "\n".join(line for line in s.split("\n") if not _is_junk_line(line, opts))


def _dedupe_adjacent_lines(s: str) -> str:
    # PDFs repeat headers/footers -- collapse consecutive duplicates.
    out: list[str] = []
    prev: str | None = None
    for line in s.split("\n"):
        key = line.strip().lower()
        if key and key == prev:
            continue
        out.append(line)
        prev = key
    return "\n".join(out)


def _truncate(s: str, max_chars: int) -> str:
    if len(s) <= max_chars:
        return s
    slice_ = s[:max_chars]
    last_space = slice_.rfind(" ")
    if last_space > max_chars * 0.8:
        return slice_[:last_space] + "…"
    return slice_ + "…"


def compress_for_skip_detection(
    text: str,
    *,
    max_chars: int = DEFAULT_MAX_CHARS,
    min_line_length: int = DEFAULT_MIN_LINE_LENGTH,
    replace_urls: bool = True,
    replace_emails: bool = True,
    drop_pure_number_lines: bool = True,
) -> str:
    """Return aggressively-compressed text suitable for an LLM skip-check.

    Returns "" for empty or non-string input.
    """
    if not isinstance(text, str) or not text:
        return ""

    opts = CompressionOptions(
        max_chars=max_chars,
        min_line_length=min_line_length,
        replace_urls=replace_urls,
        replace_emails=replace_emails,
        drop_pure_number_lines=drop_pure_number_lines,
    )

    s = text
    s = _normalize_unicode(s)
    s = _strip_control_chars(s)
    s = _asciify_punctuation(s)
    s = _rejoin_hyphenation(s)
    if opts.replace_urls:
        s = _mask_urls(s)
    if opts.replace_emails:
        s = _mask_emails(s)
    s = _strip_decorative(s)
    s = _collapse_punctuation(s)
    s = _normalize_whitespace(s)
    s = _filter_lines(s, opts)
    s = _dedupe_adjacent_lines(s)
    s = s.strip()
    s = _truncate(s, opts.max_chars)
    return s
