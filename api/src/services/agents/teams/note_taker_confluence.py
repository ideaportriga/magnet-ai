from __future__ import annotations

import datetime as dt
import hashlib
import html as html_lib
import json
import re
from logging import getLogger
from typing import Any, Awaitable, Callable

from microsoft_agents.hosting.core import TurnContext
from microsoft_agents.hosting.teams import TeamsInfo

from services.api_servers.services import call_api_server_tool
from services.api_servers.types import ApiToolCall, ApiToolCallInputParams

logger = getLogger(__name__)


async def maybe_publish_confluence_notes(
    context: TurnContext,
    *,
    settings: dict[str, Any],
    job_id: str | None,
    meeting_context: dict[str, Any] | None,
    participants: list[str] | None,
    conversation_date: str | None,
    conversation_time: str | None,
    duration: str | None,
    sections: dict[str, str],
    send_expandable_section: Callable[..., Awaitable[None]] | None = None,
) -> None:
    integration = settings.get("integration") if isinstance(settings, dict) else None
    confluence = (
        integration.get("confluence") if isinstance(integration, dict) else None
    )
    if not isinstance(confluence, dict) or not confluence.get("enabled"):
        return

    space_id = str(confluence.get("space_key") or "").strip()
    if not space_id:
        logger.warning("[teams note-taker] confluence enabled but space_id is empty")
        return

    api_server_system_name = str(confluence.get("confluence_api_server") or "").strip()
    api_tool_system_name = str(
        confluence.get("confluence_create_page_tool") or ""
    ).strip()

    if not api_server_system_name or not api_tool_system_name:
        logger.warning(
            "[teams note-taker] confluence enabled but api server/tool are missing (server=%s tool=%s)",
            api_server_system_name or None,
            api_tool_system_name or None,
        )
        return

    title = _confluence_title_from_context(
        title_template=str(confluence.get("title_template") or "").strip() or None,
        meeting=meeting_context,
        conversation_date=conversation_date,
        job_id=job_id,
    )
    parent_id = str(confluence.get("parent_id") or "").strip()

    invited_people: list[dict[str, str]] = []
    try:
        invited_people = await _get_invited_people(context)
    except Exception as err:
        logger.debug("[teams note-taker] failed to load invited people: %s", err)

    keyterms_value = str(settings.get("keyterms") or "").strip()
    base_keyterms: list[str] = []
    if keyterms_value:
        for part in re.split(r"[\n,;]+", keyterms_value):
            item = str(part or "").strip()
            if item:
                base_keyterms.append(item)

    invited_keyterms: list[str] = []
    for person in invited_people or []:
        first_name = str(person.get("first_name") or "").strip()
        last_name = str(person.get("last_name") or "").strip()
        display_name = " ".join([p for p in (first_name, last_name) if p]).strip()
        if display_name:
            invited_keyterms.append(display_name)

    merged_keyterms: list[str] = []
    seen_keyterms: set[str] = set()
    for item in [*base_keyterms, *invited_keyterms]:
        key = item.lower()
        if key in seen_keyterms:  # skip duplicates?
            continue
        seen_keyterms.add(key)
        merged_keyterms.append(item)
    keyterms_part = ", ".join(merged_keyterms) if merged_keyterms else None

    markdown_body = _build_confluence_markdown(
        meeting=meeting_context,
        participants=participants,
        invited_people=invited_people,
        keyterms=keyterms_part,
        conversation_date=conversation_date,
        conversation_time=conversation_time,
        duration=duration,
        sections=sections,
    )

    # Confluence REST v2 expects `spaceId` and `body.representation/value`.
    request_body: dict[str, Any] = _build_confluence_v2_create_page_request(
        space_id=space_id,
        title=title,
        content=markdown_body,
        parent_id=parent_id or None,
    )
    if parent_id:
        # Keep both styles to maximize compatibility with tool variants.
        request_body["parent_id"] = parent_id
        request_body["parentId"] = parent_id

    debug_payload = {
        "api_server_system_name": api_server_system_name,
        "api_tool_system_name": api_tool_system_name,
        "space_id": space_id,
        "parent_id": parent_id or None,
        "title": title,
        "content_bytes": len(markdown_body.encode("utf-8", errors="ignore")),
        "content_sha256": _hash_text_sha256(markdown_body),
        "meeting_id": str((meeting_context or {}).get("id") or "").strip() or None,
        "meeting_title": _get_meeting_title_part(meeting_context),
        "job_id": str(job_id or "").strip() or None,
    }
    logger.info("[teams note-taker] confluence publish request: %s", debug_payload)

    try:
        api_call = ApiToolCall(
            server=api_server_system_name,
            tool=api_tool_system_name,
            input_params=ApiToolCallInputParams(requestBody=request_body),
        )
        result = await call_api_server_tool(api_call)
    except Exception as err:
        logger.exception(
            "[teams note-taker] failed to publish Confluence page via API tool=%s server=%s",
            api_tool_system_name,
            api_server_system_name,
        )
        await _maybe_send_debug(
            send_expandable_section,
            context,
            title="Confluence publish debug",
            payload=debug_payload,
        )
        await _maybe_send_debug(
            send_expandable_section,
            context,
            title="Confluence error details",
            payload=_exception_debug_details(err),
        )
        await context.send_activity(
            f"Failed to publish meeting notes to Confluence: {getattr(err, 'message', str(err))}"
        )
        return

    if getattr(result, "status_code", 0) >= 400:
        status = getattr(result, "status_code", None)
        error_summary = _api_tool_error_summary(result)
        await _maybe_send_debug(
            send_expandable_section,
            context,
            title="Confluence response details",
            payload=_api_tool_result_debug_details(result),
        )
        await context.send_activity(
            "Failed to publish meeting notes to Confluence: "
            f"API tool returned status {status if status is not None else 'n/a'}"
            + (f" ({error_summary})." if error_summary else ".")
        )
        return

    page_url = _extract_confluence_page_url(getattr(result, "content", "") or "")
    if page_url:
        await context.send_activity(
            f"Published meeting notes to Confluence: {page_url}"
        )
    else:
        await context.send_activity("Published meeting notes to Confluence.")


async def _maybe_send_debug(
    send_expandable_section: Callable[..., Awaitable[None]] | None,
    context: TurnContext,
    *,
    title: str,
    payload: dict[str, Any],
) -> None:
    if send_expandable_section is None:
        return
    try:
        await send_expandable_section(
            context,
            title=title,
            content=json.dumps(payload, indent=2, sort_keys=True),
            preserve_newlines=True,
        )
    except Exception:
        return


def _safe_template_format(template: str, values: dict[str, Any]) -> str:
    if not template:
        return ""
    try:
        return template.format_map(values)
    except Exception:
        return ""


def _get_meeting_title_part(meeting: dict[str, Any] | None) -> str | None:
    if not meeting:
        return None
    title = meeting.get("title") or meeting.get("subject")
    title = str(title or "").strip()
    return title or None


def _confluence_title_from_context(
    *,
    title_template: str | None,
    meeting: dict[str, Any] | None,
    conversation_date: str | None,
    job_id: str | None,
) -> str:
    meeting_title = _get_meeting_title_part(meeting) or "Meeting"
    date_part = str(conversation_date or "").strip() or dt.datetime.now(
        dt.timezone.utc
    ).strftime("%Y-%m-%d")

    formatted = _safe_template_format(
        str(title_template or "").strip(),
        {
            "meeting_title": meeting_title,
            "date": date_part,
            "job_id": str(job_id or "").strip(),
            "meeting_id": str((meeting or {}).get("id") or "").strip(),
        },
    ).strip()
    if formatted:
        return formatted
    suffix = f" ({job_id})" if job_id else ""
    return f"Meeting notes: {meeting_title} ({date_part}){suffix}"


def _build_confluence_markdown(
    *,
    meeting: dict[str, Any] | None,
    participants: list[str] | None,
    invited_people: list[dict[str, str]] | None,
    keyterms: str | None,
    conversation_date: str | None,
    conversation_time: str | None,
    duration: str | None,
    sections: dict[str, str],
) -> str:
    meeting_title = _get_meeting_title_part(meeting) or "Meeting"
    meeting_id = str((meeting or {}).get("id") or "").strip() or "n/a"
    date_part = str(conversation_date or "").strip() or "n/a"
    time_part = str(conversation_time or "").strip() or date_part
    duration_part = str(duration or "").strip() or "n/a"
    participants_part = ", ".join([p for p in (participants or []) if p]) or "n/a"
    keyterms_part = str(keyterms or "").strip()

    parts: list[str] = [
        f"# {meeting_title}",
        "",
        f"- Recording time: {time_part}",
        f"- Duration: {duration_part}",
        f"- Meeting ID: {meeting_id}",
        f"- Participants: {participants_part}",
        *([f"- Keyterms: {keyterms_part}"] if keyterms_part else []),
        "",
    ]

    invited_items = invited_people or []
    if invited_items:
        parts.append("## Invited")
        parts.append("")
        for person in invited_items:
            first_name = str(person.get("first_name") or "").strip()
            last_name = str(person.get("last_name") or "").strip()
            email = str(person.get("email") or "").strip()
            display_name = " ".join([p for p in (first_name, last_name) if p]).strip()
            if display_name and email:
                parts.append(f"- {display_name} <{email}>")
            elif email:
                parts.append(f"- {email}")
            elif display_name:
                parts.append(f"- {display_name}")
        parts.append("")

    summary = (sections.get("summary") or "").strip()
    if summary:
        parts.extend(["## Summary", "", summary, ""])

    chapters = (sections.get("chapters") or "").strip()
    if chapters:
        parts.extend(["## Chapters", "", chapters, ""])

    return "\n".join(parts).strip() + "\n"


def _extract_confluence_page_url(payload: Any) -> str | None:
    if isinstance(payload, str) and payload.strip():
        try:
            payload = json.loads(payload)
        except Exception:
            return None

    if not isinstance(payload, dict):
        return None

    links = payload.get("_links") if isinstance(payload.get("_links"), dict) else {}
    if not links and isinstance(payload.get("links"), dict):
        links = payload.get("links") or {}

    base = str(links.get("base") or links.get("baseUrl") or "").strip()
    webui = str(
        links.get("webui")
        or links.get("webUi")
        or links.get("tinyui")
        or links.get("tinyUi")
        or ""
    ).strip()
    if base and webui:
        return f"{base}{webui}"
    return None


def _build_confluence_storage_body(content: str) -> dict[str, str]:
    html = _markdown_to_confluence_storage_html(content or "")
    return {"representation": "storage", "value": html}


_MD_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)\s*$")
_MD_BULLET_RE = re.compile(r"^\s*-\s+(.*)\s*$")
_MD_FENCE_RE = re.compile(r"^\s*```")


def _md_inline_to_storage_html(text: str) -> str:
    escaped = html_lib.escape(text or "")
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^\*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\*([^\*]+)\*", r"<em>\1</em>", escaped)
    return escaped


def _markdown_to_confluence_storage_html(markdown_text: str) -> str:
    lines = (markdown_text or "").splitlines()
    parts: list[str] = []
    paragraph: list[str] = []
    in_list = False
    in_code = False
    code_lines: list[str] = []

    def _flush_paragraph() -> None:
        nonlocal paragraph
        if not paragraph:
            return
        body = "<br/>".join(_md_inline_to_storage_html(line) for line in paragraph)
        parts.append(f"<p>{body}</p>")
        paragraph = []

    def _close_list() -> None:
        nonlocal in_list
        if in_list:
            parts.append("</ul>")
            in_list = False

    def _flush_code_block() -> None:
        nonlocal code_lines
        if not code_lines:
            return
        code = html_lib.escape("\n".join(code_lines))
        parts.append(f"<pre><code>{code}</code></pre>")
        code_lines = []

    for raw in lines:
        line = raw.rstrip("\n")

        if _MD_FENCE_RE.match(line):
            if in_code:
                in_code = False
                _flush_code_block()
            else:
                _flush_paragraph()
                _close_list()
                in_code = True
            continue

        if in_code:
            code_lines.append(line)
            continue

        if not line.strip():
            _flush_paragraph()
            _close_list()
            continue

        heading_match = _MD_HEADING_RE.match(line)
        if heading_match:
            _flush_paragraph()
            _close_list()
            level = len(heading_match.group(1))
            text = heading_match.group(2) or ""
            parts.append(f"<h{level}>{_md_inline_to_storage_html(text)}</h{level}>")
            continue

        bullet_match = _MD_BULLET_RE.match(line)
        if bullet_match:
            _flush_paragraph()
            if not in_list:
                parts.append("<ul>")
                in_list = True
            parts.append(
                f"<li>{_md_inline_to_storage_html(bullet_match.group(1) or '')}</li>"
            )
            continue

        _close_list()
        paragraph.append(line)

    if in_code:
        _flush_code_block()
    _flush_paragraph()
    _close_list()

    return "\n".join(parts).strip() or "<p></p>"


def _build_confluence_v2_create_page_request(
    *,
    space_id: str,
    title: str,
    content: str,
    parent_id: str | None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "spaceId": str(space_id),
        "status": "current",
        "title": title,
        "body": _build_confluence_storage_body(content),
    }
    if parent_id:
        body["parentId"] = str(parent_id)
    return body


async def _get_invited_people(context: TurnContext) -> list[dict[str, str]]:
    invited: list[dict[str, str]] = []
    seen: set[str] = set()
    continuation_token: str | None = None

    while True:
        paged = await TeamsInfo.get_paged_members(
            context, page_size=100, continuation_token=continuation_token
        )
        members = getattr(paged, "members", None) or []
        for member in members:
            given = (
                getattr(member, "given_name", None)
                or getattr(member, "givenName", None)
                or ""
            )
            surname = (
                getattr(member, "surname", None)
                or getattr(member, "last_name", None)
                or getattr(member, "lastName", None)
                or ""
            )
            email = (
                getattr(member, "email", None)
                or getattr(member, "user_principal_name", None)
                or getattr(member, "userPrincipalName", None)
                or ""
            )

            given = str(given or "").strip()
            surname = str(surname or "").strip()
            email = str(email or "").strip()

            if not given and not surname:
                display_name = str(getattr(member, "name", "") or "").strip()
                if display_name:
                    pieces = display_name.split()
                    if pieces:
                        given = pieces[0]
                        if len(pieces) > 1:
                            surname = " ".join(pieces[1:])

            dedupe_key = (email or str(getattr(member, "id", "") or "")).strip()
            if not dedupe_key or dedupe_key in seen:
                continue
            seen.add(dedupe_key)

            invited.append(
                {
                    "first_name": given,
                    "last_name": surname,
                    "email": email,
                }
            )

        continuation_token = getattr(paged, "continuation_token", None)
        if not continuation_token:
            break

    invited.sort(
        key=lambda p: (
            (p.get("last_name") or "").lower(),
            (p.get("first_name") or "").lower(),
            (p.get("email") or "").lower(),
        )
    )
    return invited


def _hash_text_sha256(text: str) -> str:
    try:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
    except Exception:
        return ""


def _safe_truncate(text: Any, limit: int = 8000) -> str:
    if not isinstance(text, str):
        try:
            text = json.dumps(text, ensure_ascii=False)
        except Exception:
            text = str(text)
    if limit <= 0:
        return ""
    if len(text) <= limit:
        return text
    return text[:limit] + f"\\n…(truncated, {len(text)} chars total)"


def _exception_debug_details(err: Exception) -> dict[str, Any]:
    details: dict[str, Any] = {
        "type": f"{err.__class__.__module__}.{err.__class__.__name__}",
        "message": getattr(err, "message", None) or str(err),
        "repr": repr(err),
    }

    response = getattr(err, "response", None)
    if response is not None:
        details["http_status"] = getattr(response, "status_code", None)
        details["http_url"] = str(getattr(response, "url", "") or "") or None
        try:
            details["http_body"] = _safe_truncate(getattr(response, "text", "") or "")
        except Exception:
            details["http_body"] = None
        try:
            details["http_json"] = response.json()
        except Exception:
            details["http_json"] = None

    details["aiohttp_status"] = getattr(err, "status", None)
    details["aiohttp_headers"] = getattr(err, "headers", None)

    return details


def _api_tool_result_debug_details(result: Any) -> dict[str, Any]:
    return {
        "status_code": getattr(result, "status_code", None),
        "headers": getattr(result, "headers", None),
        "content": _safe_truncate(getattr(result, "content", "") or ""),
    }


# TODO: Standartize note taker error handling across API tools (use it also for sf)
def _api_tool_error_summary(result: Any, *, limit: int = 220) -> str | None:
    """
    Extract a short, user-facing error summary from an API tool response.

    The raw details are still available via `_api_tool_result_debug_details`.
    """

    def _clean(text: Any) -> str:
        text = "" if text is None else str(text)
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            return ""
        if limit > 0 and len(text) > limit:
            return text[: max(0, limit - 3)] + "..."
        return text

    content = getattr(result, "content", None)
    if content is None:
        return None

    if isinstance(content, (dict, list)):
        payload = content
    else:
        raw = str(content or "").strip()
        if not raw:
            return None
        payload = None
        if raw[:1] in "{[":
            try:
                payload = json.loads(raw)
            except Exception:
                payload = None

    if isinstance(payload, dict):
        # Common patterns across Confluence / gateways / proxies.
        for key in ("message", "error", "title", "detail", "reason"):
            if key in payload:
                msg = _clean(payload.get(key))
                if msg:
                    return msg

        errors = payload.get("errors")
        if isinstance(errors, list) and errors:
            first = errors[0]
            if isinstance(first, dict):
                msg = _clean(
                    first.get("message") or first.get("detail") or first.get("reason")
                )
                if msg:
                    return msg
            msg = _clean(first)
            if msg:
                return msg

        status_code = payload.get("statusCode") or payload.get("status")
        if status_code is not None:
            msg = _clean(payload.get("message"))
            if msg:
                return f"{status_code}: {msg}"

        return _clean(json.dumps(payload, ensure_ascii=False))

    if isinstance(payload, list):
        return _clean(json.dumps(payload, ensure_ascii=False))

    return _clean(content)
