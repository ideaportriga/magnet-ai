import re
from uuid import uuid4

# Matches <img> tags with base64 data URIs in the src attribute
_BASE64_IMG_RE = re.compile(
    r"<img\s[^>]*?src\s*=\s*\"data:image/[^\"]*;base64,[^\"]*\"[^>]*/?>",
    re.IGNORECASE | re.DOTALL,
)

# Matches <svg ...>...</svg> blocks (non-greedy, dotall)
_SVG_RE = re.compile(
    r"<svg[\s>][\s\S]*?</svg>",
    re.IGNORECASE,
)

_PLACEHOLDER_RE = re.compile(r"\[IMAGE:([0-9a-f\-]{36})\]")


def strip_images(text: str, registry: dict[str, str]) -> str:
    """Replace base64 <img> tags and <svg> blocks with UUID placeholders.

    Each replaced image is stored in *registry* (uuid -> original html)
    so it can be restored later with :func:`restore_images`.
    """
    if not text:
        return text

    def _replace(match: re.Match[str]) -> str:
        uid = str(uuid4())
        registry[uid] = match.group(0)
        return f"[IMAGE:{uid}]"

    text = _BASE64_IMG_RE.sub(_replace, text)
    text = _SVG_RE.sub(_replace, text)
    return text


def restore_images(text: str, registry: dict[str, str]) -> str:
    """Replace ``[IMAGE:<uuid>]`` placeholders back with original HTML."""
    if not text or not registry:
        return text

    def _restore(match: re.Match[str]) -> str:
        uid = match.group(1)
        return registry.get(uid, match.group(0))

    return _PLACEHOLDER_RE.sub(_restore, text)
