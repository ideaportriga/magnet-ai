"""Content-vs-extension MIME validation for file uploads (§C.1).

The codebase already runs `kreuzberg.detect_mime_type` on upload bytes, but
historically it only recorded the detected MIME — a `.pdf` with JPEG content
was still accepted. This module refuses that mismatch and enforces an
allow-list of MIME types that any whitelisted extension may legitimately
produce.
"""

from __future__ import annotations

from logging import getLogger

from litestar.exceptions import ClientException

logger = getLogger(__name__)

# Extension → set of MIME types that `kreuzberg.detect_mime_type` may return
# for valid content of that extension. Kept explicit (not `mimetypes`) because
# python's mimetypes is too permissive (e.g. text/plain for many things).
EXTENSION_MIME_WHITELIST: dict[str, frozenset[str]] = {
    ".pdf": frozenset({"application/pdf"}),
    ".doc": frozenset({"application/msword"}),
    ".docx": frozenset(
        {
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            # Some detectors return the generic zip type for docx containers.
            "application/zip",
        }
    ),
    ".xls": frozenset({"application/vnd.ms-excel"}),
    ".xlsx": frozenset(
        {
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/zip",
        }
    ),
    ".ppt": frozenset({"application/vnd.ms-powerpoint"}),
    ".pptx": frozenset(
        {
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "application/zip",
        }
    ),
    ".odt": frozenset({"application/vnd.oasis.opendocument.text", "application/zip"}),
    ".ods": frozenset(
        {"application/vnd.oasis.opendocument.spreadsheet", "application/zip"}
    ),
    ".odp": frozenset(
        {"application/vnd.oasis.opendocument.presentation", "application/zip"}
    ),
    ".rtf": frozenset({"application/rtf", "text/rtf"}),
    ".epub": frozenset({"application/epub+zip", "application/zip"}),
    ".csv": frozenset({"text/csv", "text/plain"}),
    ".html": frozenset({"text/html", "text/plain"}),
    ".htm": frozenset({"text/html", "text/plain"}),
    ".xml": frozenset({"application/xml", "text/xml", "text/plain"}),
    ".txt": frozenset({"text/plain"}),
    ".md": frozenset({"text/plain", "text/markdown"}),
    ".json": frozenset({"application/json", "text/plain"}),
    ".png": frozenset({"image/png"}),
    ".jpg": frozenset({"image/jpeg"}),
    ".jpeg": frozenset({"image/jpeg"}),
    ".gif": frozenset({"image/gif"}),
    ".webp": frozenset({"image/webp"}),
    ".bmp": frozenset({"image/bmp", "image/x-ms-bmp"}),
    ".tiff": frozenset({"image/tiff"}),
    ".tif": frozenset({"image/tiff"}),
    ".eml": frozenset({"message/rfc822", "text/plain"}),
    ".msg": frozenset({"application/vnd.ms-outlook", "application/x-ole-storage"}),
    ".wav": frozenset({"audio/wav", "audio/x-wav"}),
    ".mp3": frozenset({"audio/mpeg"}),
    ".m4a": frozenset({"audio/mp4", "audio/x-m4a"}),
}

# Detected MIMEs explicitly refused even if extension matches. An executable
# with a renamed extension is the prototypical attack here.
BLOCKED_DETECTED_MIMES: frozenset[str] = frozenset(
    {
        "application/x-dosexec",
        "application/x-executable",
        "application/x-mach-binary",
        "application/x-msdownload",
        "application/x-sharedlib",
        "application/vnd.microsoft.portable-executable",
        "application/x-msi",
    }
)


def validate_upload_mime(filename: str, detected_mime: str) -> None:
    """Reject extension↔content mismatch and always-blocked MIME types.

    Called after `kreuzberg.detect_mime_type` has run on the raw bytes.
    Raises ClientException(422-ish) with a human message; callers don't need
    to translate.
    """
    import os

    ext = os.path.splitext(filename)[1].lower()

    # Explicit blocklist wins regardless of extension.
    if detected_mime in BLOCKED_DETECTED_MIMES:
        logger.warning(
            "Rejected upload: blocked MIME %s for %s",
            detected_mime,
            filename,
        )
        raise ClientException(f"File content type '{detected_mime}' is not allowed.")

    allowed = EXTENSION_MIME_WHITELIST.get(ext)
    if allowed is None:
        # Extension handling is the caller's responsibility; mime_validation
        # only speaks about content. If caller passes an unknown extension,
        # be strict rather than silently allowing it.
        raise ClientException(f"Unsupported file extension '{ext}'.")

    # application/octet-stream is what kreuzberg returns when it can't tell.
    # We intentionally allow it — blocking it would break uploads of
    # legitimate but obscure file variants; the extension has already been
    # whitelisted by the caller.
    if detected_mime == "application/octet-stream":
        return

    if detected_mime not in allowed:
        logger.warning(
            "Rejected upload: extension/content mismatch for %s (ext=%s, detected=%s, allowed=%s)",
            filename,
            ext,
            detected_mime,
            sorted(allowed),
        )
        raise ClientException(
            f"File content ({detected_mime}) does not match extension '{ext}'."
        )
