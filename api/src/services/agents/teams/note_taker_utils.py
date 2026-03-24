import datetime as dt
import html as html_lib
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


_URL_RE = re.compile(r"(https?://[^\s<>\"]+)", re.IGNORECASE)


class _AnchorHrefExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        for key, value in attrs:
            if key.lower() == "href" and value:
                self.hrefs.append(value)


def _extract_first_url(text: str) -> str | None:
    if not text:
        return None
    match = _URL_RE.search(text)
    if not match:
        return None
    url = (match.group(1) or "").strip()
    url = url.rstrip(").,>\"'")
    return url if url.lower().startswith(("http://", "https://")) else None


def _extract_first_url_from_attachments(activity: Any) -> str | None:
    attachments = getattr(activity, "attachments", None) or []
    for attachment in attachments:
        content_url = getattr(attachment, "content_url", None)
        if isinstance(content_url, str):
            url = _extract_first_url(content_url)
            if url:
                return url

        content = getattr(attachment, "content", None)
        if isinstance(content, str) and content:
            try:
                parser = _AnchorHrefExtractor()
                parser.feed(content)
                for href in parser.hrefs:
                    url = _extract_first_url(html_lib.unescape(href).strip())
                    if url:
                        return url
            except Exception:
                pass
        elif isinstance(content, dict) and content:
            for value in content.values():
                if isinstance(value, str):
                    url = _extract_first_url(value)
                    if url:
                        return url

    return None


_DEFAULT_NOTE_TAKER_SETTINGS: dict[str, Any] = {
    "subscription_recordings_ready": False,
    "pipeline_id": "elevenlabs",
    "send_number_of_speakers": False,
    "create_knowledge_graph_embedding": False,
    "knowledge_graph_system_name": "",
    "keyterms": "",
    "integration": {
        "confluence": {
            "enabled": False,
            "confluence_api_server": "",
            "confluence_create_page_tool": "",
            "space_key": "",
            "parent_id": "",
            "title_template": "Meeting notes: {meeting_title} ({date})",
        },
        "salesforce": {
            "send_transcript_to_salesforce": False,
            "salesforce_api_server": "",
            "salesforce_stt_recording_tool": "",
        },
    },
    "chapters": {"enabled": False, "prompt_template": ""},
    "summary": {"enabled": False, "prompt_template": ""},
    "insights": {"enabled": False, "prompt_template": ""},
    "post_transcription": {"enabled": False, "prompt_template": ""},
}


def _merge_note_taker_settings(raw: dict[str, Any] | None) -> dict[str, Any]:
    settings = dict(_DEFAULT_NOTE_TAKER_SETTINGS)
    if not isinstance(raw, dict):
        return settings

    for key in (
        "subscription_recordings_ready",
        "pipeline_id",
        "send_number_of_speakers",
        "create_knowledge_graph_embedding",
        "knowledge_graph_system_name",
        "keyterms",
    ):
        if key in raw:
            settings[key] = raw[key]

    default_integration = dict(settings.get("integration") or {})
    raw_integration = raw.get("integration")
    if isinstance(raw_integration, dict):
        merged_integration: dict[str, Any] = dict(default_integration)
        for integration_key, integration_value in raw_integration.items():
            if isinstance(integration_value, dict) and isinstance(
                merged_integration.get(integration_key), dict
            ):
                merged_integration[integration_key] = {
                    **(merged_integration.get(integration_key) or {}),
                    **integration_value,
                }
            else:
                merged_integration[integration_key] = integration_value
        settings["integration"] = merged_integration
    else:
        settings["integration"] = default_integration

    for section in ("chapters", "summary", "insights", "post_transcription"):
        base_section = dict(settings[section])
        section_raw = raw.get(section)
        if isinstance(section_raw, dict):
            for key in base_section.keys():
                if key in section_raw:
                    base_section[key] = section_raw[key]
        settings[section] = base_section

    return settings


def _format_duration(seconds: float | int | None) -> str:
    if seconds is None:
        return "Unknown"
    try:
        total_seconds = float(seconds)
    except (TypeError, ValueError):
        return "Unknown"
    if total_seconds < 0:
        return "Unknown"

    whole_seconds = int(total_seconds)
    hours, remainder = divmod(whole_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    fractional = total_seconds - whole_seconds
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    if minutes > 0:
        return f"{minutes}m {secs}s"
    if fractional:
        return f"{total_seconds:.1f}s"
    return f"{secs}s"


def _format_mm_ss(seconds: float | int | None) -> str:
    try:
        total_seconds = int(float(seconds))
    except (TypeError, ValueError):
        return "00:00"
    total_seconds = max(total_seconds, 0)
    minutes, secs = divmod(total_seconds, 60)
    return f"{minutes:02d}:{secs:02d}"


def _format_file_size(size_bytes: int | None) -> str:
    if size_bytes is None:
        return "Unknown"
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    if size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def _format_recording_datetime(iso_datetime: str | None) -> tuple[str, str]:
    if not iso_datetime:
        return ("Unknown date", "Unknown time")
    try:
        dt_obj = dt.datetime.fromisoformat(iso_datetime.replace("Z", "+00:00"))
        date_str = dt_obj.strftime("%b %d, %Y")
        time_str = dt_obj.strftime("%I:%M %p UTC")
        return (date_str, time_str)
    except Exception:
        return (iso_datetime, "")


def _format_recording_date_iso(iso_datetime: str | None) -> str | None:
    if not iso_datetime:
        return None
    try:
        dt_obj = dt.datetime.fromisoformat(iso_datetime.replace("Z", "+00:00"))
    except Exception:
        return None
    return dt_obj.date().isoformat()


def _format_recording_datetime_utc_label(iso_datetime: str | None) -> str | None:
    if not iso_datetime:
        return None
    try:
        dt_obj = dt.datetime.fromisoformat(iso_datetime.replace("Z", "+00:00"))
        dt_obj = dt_obj.astimezone(dt.timezone.utc)
    except Exception:
        return None
    return dt_obj.strftime("%Y-%m-%d %H:%M UTC")


def _format_recording_date_compact(iso_datetime: str | None) -> str | None:
    if not iso_datetime:
        return None
    try:
        dt_obj = dt.datetime.fromisoformat(iso_datetime.replace("Z", "+00:00"))
    except Exception:
        return None
    return dt_obj.strftime("%Y%m%d")


def _parse_content_disposition_filename(header_value: str | None) -> str | None:
    if not header_value:
        return None
    parts = header_value.split(";")
    for part in parts:
        part = part.strip()
        if part.lower().startswith("filename*="):
            value = part.split("=", 1)[1]
            if "''" in value:
                value = value.split("''", 1)[1]
            return value.strip("\"'")
        if part.lower().startswith("filename="):
            value = part.split("=", 1)[1]
            return value.strip("\"'")
    return None


def _guess_filename_from_link(link: str) -> str:
    parsed = urlparse(link)
    filename = Path(parsed.path).name
    if filename:
        return filename

    query = parse_qs(parsed.query)
    file_urls = (
        query.get("fileUrl")
        or query.get("fileurl")
        or query.get("file_url")
        or query.get("file")
    )
    if file_urls:
        nested_url = file_urls[0]
        nested_parsed = urlparse(nested_url)
        nested_name = Path(nested_parsed.path).name
        if nested_name:
            return nested_name

    return "file"


def _format_iso_datetime(value: str | None) -> str:
    if not value:
        return "Unknown"
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return value


def _normalize_filename_part(value: str) -> str:
    ascii_value = value.encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", ascii_value).strip("-")
    return cleaned or "item"


def _truncate_filename(base: str, ext: str, max_len: int = 255) -> str:
    ext = ext if ext.startswith(".") else f".{ext}" if ext else ""
    max_base_len = max_len - len(ext)
    if max_base_len <= 0:
        return ext[:max_len]
    if len(base) > max_base_len:
        base = base[:max_base_len].rstrip("-")
    return f"{base}{ext}"


def parse_keyterms_list(value: str | None) -> list[str]:
    text = str(value or "").strip()
    if not text:
        return []
    parts = re.split(r"[\n,;]+", text)
    return [p.strip() for p in parts if str(p or "").strip()]


def merge_unique_strings(*lists: list[str] | None) -> list[str]:
    items: list[str] = []
    for lst in lists:
        if lst:
            items.extend(lst)
    if not items:
        return []

    seen: set[str] = set()
    merged: list[str] = []
    for item in items:
        text = str(item or "").strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        merged.append(text)
    return merged


def keyterms_to_display(keyterms: list[str] | None) -> str | None:
    terms = [str(t or "").strip() for t in (keyterms or []) if str(t or "").strip()]
    return ", ".join(terms) if terms else None


def _build_note_taker_filename(
    *,
    kind: str,
    meeting_id: str | None,
    item_id: str | None,
    date_part: str | None,
    ext: str,
) -> str:
    parts = [
        "note-taker",
        kind,
        meeting_id or "meeting",
        item_id or "item",
        date_part or "",
    ]
    normalized = [_normalize_filename_part(part) for part in parts if part]
    base = "-".join(normalized)
    return _truncate_filename(base, ext)


def _get_meeting_title_part(meeting: dict[str, Any] | None) -> str | None:
    if not meeting:
        return None
    title = meeting.get("title") or meeting.get("subject")
    title = str(title or "").strip()
    return title or None


def _get_meeting_id_part(meeting: dict[str, Any] | None) -> str | None:
    if not meeting:
        return None
    return (
        meeting.get("id")
        or meeting.get("conversationId")
        or meeting.get("meetingId")
        or meeting.get("meeting_id")
        or meeting.get("chat_id")
    )


def _build_recording_filename(
    meeting: dict[str, Any], recording: dict[str, Any], content_url: str
) -> str:
    meeting_part = (
        _get_meeting_title_part(meeting) or _get_meeting_id_part(meeting) or "meeting"
    )
    date_part = _format_recording_date_compact(recording.get("createdDateTime"))
    ext = Path(urlparse(content_url).path).suffix or ".mp4"
    parts = ["note-taker", "recording", str(meeting_part), str(date_part or "").strip()]
    normalized = [_normalize_filename_part(part) for part in parts if part]
    base = "-".join(normalized)
    return _truncate_filename(base, ext)


def _parse_content_length(value: str | None) -> int | None:
    if not value:
        return None
    try:
        length = int(value)
    except ValueError:
        return None
    return length if length > 0 else None
