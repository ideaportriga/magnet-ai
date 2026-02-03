from __future__ import annotations

import datetime as dt
import hashlib
import html as html_lib
import json
import re
from logging import getLogger
from typing import Any, Awaitable, Callable

import aiohttp

from microsoft_agents.hosting.core import TurnContext

from core.config.app import alchemy
from core.domain.api_servers.service import ApiServersService
from services.api_servers.clients import create_api_client_session
from services.api_servers.types import ApiServerConfigWithSecrets
from .note_taker_people import get_invited_people, invited_people_to_names
from .note_taker_utils import (
    keyterms_to_display,
    merge_unique_strings,
    parse_keyterms_list,
)

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
    transcript: str | None = None,
    keyterms: list[str] | None = None,
    invited_people: list[dict[str, str]] | None = None,
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

    if invited_people is None:
        try:
            invited_people = await get_invited_people(context)
        except Exception as err:
            logger.debug("[teams note-taker] failed to load invited people: %s", err)
            invited_people = []

    if keyterms is None:
        keyterms = merge_unique_strings(
            parse_keyterms_list(str(settings.get("keyterms") or "")),
            invited_people_to_names(invited_people),
        )

    keyterms_part = keyterms_to_display(keyterms)

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
        "attach_transcript": bool(transcript and str(transcript).strip()),
    }
    logger.info("[teams note-taker] confluence publish request: %s", debug_payload)

    try:
        wiki_base_url, confluence_session = await _create_confluence_http_session(
            api_server_system_name
        )
        async with confluence_session:
            existing = None
            try:
                existing = await _find_confluence_page_by_title(
                    confluence_session,
                    wiki_base_url,
                    space_id=space_id,
                    title=title,
                )
            except Exception as search_err:
                logger.warning(
                    "[teams note-taker] confluence page search failed; continuing with create (space_id=%s title=%s): %s",
                    space_id,
                    title,
                    getattr(search_err, "message", str(search_err)),
                )
                await _maybe_send_debug(
                    send_expandable_section,
                    context,
                    title="Confluence search error (non-fatal)",
                    payload={
                        "wiki_base_url": wiki_base_url,
                        "space_id": space_id,
                        "title": title,
                        "error": _exception_debug_details(search_err),
                    },
                )

            # Confluence REST v2 expects `spaceId` and `body.representation/value`.
            if existing and existing.get("id"):
                page_id = str(existing.get("id"))
                current_version = _extract_confluence_version_number(existing)
                if current_version is None:
                    page_payload = await _get_confluence_v2_page(
                        confluence_session,
                        wiki_base_url,
                        page_id=page_id,
                    )
                    current_version = _extract_confluence_version_number(page_payload)
                if current_version is None:
                    raise RuntimeError(
                        "Confluence page update failed: could not resolve current page version."
                    )
                request_body = _build_confluence_v2_update_page_request(
                    page_id=page_id,
                    space_id=space_id,
                    title=title,
                    content=markdown_body,
                    parent_id=parent_id or None,
                    next_version=current_version + 1,
                )
                try:
                    result_payload = await _update_confluence_v2_page(
                        confluence_session,
                        wiki_base_url,
                        page_id=page_id,
                        request_body=request_body,
                    )
                except Exception as update_err:
                    # If version conflicts / required version issues happen,
                    # re-fetch the current version and retry once.
                    page_payload = await _get_confluence_v2_page(
                        confluence_session,
                        wiki_base_url,
                        page_id=page_id,
                    )
                    retry_version = _extract_confluence_version_number(page_payload)
                    if retry_version is None:
                        raise update_err
                    retry_body = _build_confluence_v2_update_page_request(
                        page_id=page_id,
                        space_id=space_id,
                        title=title,
                        content=markdown_body,
                        parent_id=parent_id or None,
                        next_version=retry_version + 1,
                    )
                    result_payload = await _update_confluence_v2_page(
                        confluence_session,
                        wiki_base_url,
                        page_id=page_id,
                        request_body=retry_body,
                    )
                published_action = "Updated"
            else:
                request_body = _build_confluence_v2_create_page_request(
                    space_id=space_id,
                    title=title,
                    content=markdown_body,
                    parent_id=parent_id or None,
                )
                try:
                    result_payload = await _create_confluence_v2_page(
                        confluence_session,
                        wiki_base_url,
                        request_body=request_body,
                    )
                    published_action = "Published"
                except Exception as create_err:
                    # Race / eventual consistency safety: if the create failed because
                    # the title already exists, re-search and update instead.
                    create_err_text = getattr(create_err, "message", None) or str(
                        create_err
                    )
                    if "status=409" not in create_err_text and "already exists" not in (
                        create_err_text.lower()
                    ):
                        raise create_err
                    try:
                        existing_after = await _find_confluence_page_by_title(
                            confluence_session,
                            wiki_base_url,
                            space_id=space_id,
                            title=title,
                        )
                    except Exception:
                        existing_after = None
                    if existing_after and existing_after.get("id"):
                        page_id = str(existing_after.get("id"))
                        current_version = _extract_confluence_version_number(
                            existing_after
                        )
                        if current_version is None:
                            page_payload = await _get_confluence_v2_page(
                                confluence_session,
                                wiki_base_url,
                                page_id=page_id,
                            )
                            current_version = _extract_confluence_version_number(
                                page_payload
                            )
                        if current_version is None:
                            raise RuntimeError(
                                "Confluence page update failed: could not resolve current page version."
                            )
                        update_body = _build_confluence_v2_update_page_request(
                            page_id=page_id,
                            space_id=space_id,
                            title=title,
                            content=markdown_body,
                            parent_id=parent_id or None,
                            next_version=current_version + 1,
                        )
                        try:
                            result_payload = await _update_confluence_v2_page(
                                confluence_session,
                                wiki_base_url,
                                page_id=page_id,
                                request_body=update_body,
                            )
                        except Exception as update_err:
                            # If version conflicts / required version issues happen,
                            # re-fetch the current version and retry once.
                            page_payload = await _get_confluence_v2_page(
                                confluence_session,
                                wiki_base_url,
                                page_id=page_id,
                            )
                            retry_version = _extract_confluence_version_number(
                                page_payload
                            )
                            if retry_version is None:
                                raise update_err
                            retry_body = _build_confluence_v2_update_page_request(
                                page_id=page_id,
                                space_id=space_id,
                                title=title,
                                content=markdown_body,
                                parent_id=parent_id or None,
                                next_version=retry_version + 1,
                            )
                            result_payload = await _update_confluence_v2_page(
                                confluence_session,
                                wiki_base_url,
                                page_id=page_id,
                                request_body=retry_body,
                            )
                        existing = existing_after
                        published_action = "Updated"
                    else:
                        raise create_err

            page_id = str(
                (result_payload or {}).get("id") or (existing or {}).get("id") or ""
            ).strip()
            page_url = _extract_confluence_page_url(result_payload or {})

            if page_url:
                await context.send_activity(
                    f"{published_action} meeting notes to Confluence: {page_url}"
                )
            else:
                await context.send_activity(
                    f"{published_action} meeting notes to Confluence."
                )

            if transcript and str(transcript).strip() and page_id:
                try:
                    await _attach_confluence_transcript(
                        confluence_session,
                        wiki_base_url,
                        page_id=page_id,
                        title=title,
                        transcript=str(transcript),
                        job_id=job_id,
                    )
                except Exception as err:
                    logger.exception(
                        "[teams note-taker] failed to attach transcript to Confluence page_id=%s",
                        page_id,
                    )
                    await context.send_activity(
                        "Meeting notes were published to Confluence, but attaching the transcript failed: "
                        f"{getattr(err, 'message', str(err))}"
                    )
    except Exception as err:
        logger.exception(
            "[teams note-taker] failed to publish Confluence page (server=%s tool=%s)",
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


def _build_confluence_v2_update_page_request(
    *,
    page_id: str,
    space_id: str,
    title: str,
    content: str,
    parent_id: str | None,
    next_version: int,
) -> dict[str, Any]:
    body = _build_confluence_v2_create_page_request(
        space_id=space_id,
        title=title,
        content=content,
        parent_id=parent_id,
    )
    body["id"] = str(page_id)
    body["version"] = {"number": int(next_version)}
    return body


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


async def _create_confluence_http_session(
    api_server_system_name: str,
) -> tuple[str, aiohttp.ClientSession]:
    async with alchemy.get_session() as session:
        api_servers_service = ApiServersService(session=session)
        api_server_schema = await api_servers_service.get_with_secrets_by_system_name(
            api_server_system_name
        )

    base_url = str(getattr(api_server_schema, "url", "") or "").strip()
    if not base_url:
        raise ValueError(
            f"Confluence API server url is empty ({api_server_system_name})."
        )

    wiki_base_url = _normalize_confluence_wiki_base_url(base_url)

    server_config = ApiServerConfigWithSecrets(
        name=api_server_schema.name,
        system_name=api_server_schema.system_name,
        url=api_server_schema.url,
        custom_headers=api_server_schema.custom_headers,
        security_scheme=api_server_schema.security_scheme,
        security_values=api_server_schema.security_values,
        verify_ssl=api_server_schema.verify_ssl,
        tools=None,
        secrets=api_server_schema.secrets_encrypted,
    )
    client_session = await create_api_client_session(server_config)
    return wiki_base_url, client_session


def _normalize_confluence_wiki_base_url(url: str) -> str:
    """
    Normalize Confluence base URL to the `/wiki` root.

    The stored API server URL may be configured as:
    - https://<site>.atlassian.net
    - https://<site>.atlassian.net/wiki
    - https://<site>.atlassian.net/wiki/api/v2
    - https://<site>.atlassian.net/wiki/rest/api
    This helper normalizes all of the above to https://<site>.atlassian.net/wiki
    so we can reliably build `/api/v2/...` and `/rest/api/...` paths.
    """
    base = str(url or "").strip()
    if not base:
        return ""
    base = base.rstrip("/")
    marker = "/wiki"
    idx = base.find(marker)
    if idx >= 0:
        return base[: idx + len(marker)]
    return f"{base}{marker}"


def _safe_parse_json(text: str) -> dict[str, Any] | list[Any] | None:
    if not isinstance(text, str) or not text.strip():
        return None
    try:
        return json.loads(text)
    except Exception:
        return None


async def _find_confluence_page_by_title(
    session: aiohttp.ClientSession,
    wiki_base_url: str,
    *,
    space_id: str,
    title: str,
) -> dict[str, Any] | None:
    url = f"{wiki_base_url}/api/v2/pages"
    params = {
        "space-id": str(space_id),
        "title": title,
        "status": "current",
        "limit": "5",
    }
    async with session.get(url, params=params) as resp:
        body_text = await resp.text()
        if resp.status == 404:
            # Some Confluence setups / proxies may not expose the search endpoint.
            # Treat as "not found" and let the caller proceed with create.
            return None
        if resp.status >= 400:
            raise RuntimeError(
                f"Confluence page search failed (status={resp.status}): {_safe_truncate(body_text, 400)}"
            )

    payload = _safe_parse_json(body_text)
    if not isinstance(payload, dict):
        return None

    results = payload.get("results")
    if not isinstance(results, list) or not results:
        return None

    # Confluence should enforce title uniqueness within a space. If it doesn't,
    # take the first exact title match, otherwise the first result.
    for item in results:
        if isinstance(item, dict) and str(item.get("title") or "") == title:
            return item
    return results[0] if isinstance(results[0], dict) else None


async def _get_confluence_v2_page(
    session: aiohttp.ClientSession,
    wiki_base_url: str,
    *,
    page_id: str,
) -> dict[str, Any]:
    url = f"{wiki_base_url}/api/v2/pages/{page_id}"
    async with session.get(url) as resp:
        body_text = await resp.text()
        if resp.status >= 400:
            raise RuntimeError(
                f"Confluence page get failed (status={resp.status}): {_safe_truncate(body_text, 400)}"
            )
    payload = _safe_parse_json(body_text)
    return payload if isinstance(payload, dict) else {}


def _extract_confluence_version_number(payload: dict[str, Any] | None) -> int | None:
    if not isinstance(payload, dict):
        return None
    version = payload.get("version")
    if isinstance(version, dict):
        raw = version.get("number") or version.get("Number")
        try:
            num = int(raw)
            return num if num > 0 else None
        except Exception:
            return None
    return None


async def _create_confluence_v2_page(
    session: aiohttp.ClientSession,
    wiki_base_url: str,
    *,
    request_body: dict[str, Any],
) -> dict[str, Any]:
    url = f"{wiki_base_url}/api/v2/pages"
    async with session.post(url, json=request_body) as resp:
        body_text = await resp.text()
        if resp.status == 409:
            raise RuntimeError(
                f"Confluence page already exists (status=409): {_safe_truncate(body_text, 400)}"
            )
        if resp.status >= 400:
            raise RuntimeError(
                f"Confluence page create failed (status={resp.status}): {_safe_truncate(body_text, 400)}"
            )
    payload = _safe_parse_json(body_text)
    if isinstance(payload, dict):
        return payload
    return {}


async def _update_confluence_v2_page(
    session: aiohttp.ClientSession,
    wiki_base_url: str,
    *,
    page_id: str,
    request_body: dict[str, Any],
) -> dict[str, Any]:
    url = f"{wiki_base_url}/api/v2/pages/{page_id}"
    async with session.put(url, json=request_body) as resp:
        body_text = await resp.text()
        if resp.status >= 400:
            raise RuntimeError(
                f"Confluence page update failed (status={resp.status}): {_safe_truncate(body_text, 400)}"
            )
    payload = _safe_parse_json(body_text)
    if isinstance(payload, dict):
        return payload
    return {}


async def _attach_confluence_transcript(
    session: aiohttp.ClientSession,
    wiki_base_url: str,
    *,
    page_id: str,
    title: str,
    transcript: str,
    job_id: str | None,
) -> None:
    url = f"{wiki_base_url}/rest/api/content/{page_id}/child/attachment"
    safe_job_id = str(job_id or "").strip() or "n-a"
    page_version = None
    try:
        page_payload = await _get_confluence_v2_page(
            session, wiki_base_url, page_id=str(page_id)
        )
        page_version = _extract_confluence_version_number(page_payload)
    except Exception:
        page_version = None

    version_part = f"v{page_version}" if isinstance(page_version, int) else "vna"
    filename = f"transcript-{version_part}-{safe_job_id}.txt"
    transcript_text = transcript.rstrip() + "\n"
    payload_bytes = transcript_text.encode("utf-8", errors="replace")

    comment = f"Transcript uploaded by Teams Note Taker (job={job_id or 'n/a'}, title={title})."

    async def _post_form(
        form: aiohttp.FormData,
        *,
        query_params: dict[str, str] | None = None,
    ) -> None:
        # Some API server configs include a default `Content-Type` header (e.g. application/json).
        # That breaks multipart parsing on Confluence side. Explicitly set boundary content type.
        multipart = form()
        headers = {
            "X-Atlassian-Token": "no-check",
            "Content-Type": getattr(multipart, "content_type", "multipart/form-data"),
        }
        async with session.post(
            url, data=multipart, headers=headers, params=query_params
        ) as resp:
            body_text = await resp.text()
            if resp.status >= 400:
                raise RuntimeError(
                    f"Confluence attachment upload failed (status={resp.status}): {_safe_truncate(body_text, 400)}"
                )

    # Attempt 1: standard Confluence multipart (file + comment).
    try:
        form = aiohttp.FormData()
        form.add_field(
            "file",
            payload_bytes,
            filename=filename,
            content_type="text/plain; charset=utf-8",
        )
        form.add_field("comment", comment)
        await _post_form(form)
        return
    except Exception as err:
        message = getattr(err, "message", None) or str(err)
        if (
            "Cannot add a new attachment with same file name as an existing attachment"
            in message
        ):
            # Should be unlikely with job_id-based filenames, but handle gracefully.
            alt_filename = f"{filename.rsplit('.', 1)[0]}-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d-%H%M%S')}.txt"
            form = aiohttp.FormData()
            form.add_field(
                "file",
                payload_bytes,
                filename=alt_filename,
                content_type="text/plain; charset=utf-8",
            )
            form.add_field("comment", comment)
            await _post_form(form)
            return
        if "Must be same number of attachment files and comments" not in message:
            raise

    # Attempt 2: omit comment (some Confluence variants/proxies are picky about comment parsing).
    try:
        form = aiohttp.FormData()
        form.add_field(
            "file",
            payload_bytes,
            filename=filename,
            content_type="text/plain; charset=utf-8",
        )
        await _post_form(form)
        return
    except Exception as err:
        message = getattr(err, "message", None) or str(err)
        if (
            "Cannot add a new attachment with same file name as an existing attachment"
            in message
        ):
            alt_filename = f"{filename.rsplit('.', 1)[0]}-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d-%H%M%S')}.txt"
            form = aiohttp.FormData()
            form.add_field(
                "file",
                payload_bytes,
                filename=alt_filename,
                content_type="text/plain; charset=utf-8",
            )
            await _post_form(form)
            return
        if "Must be same number of attachment files and comments" not in message:
            raise

    # Attempt 3: send comment via query string instead of multipart field.
    form = aiohttp.FormData()
    form.add_field(
        "file",
        payload_bytes,
        filename=filename,
        content_type="text/plain; charset=utf-8",
    )
    await _post_form(form, query_params={"comment": comment})
