"""Salesforce integration helpers for Teams note-taker."""

import json
import datetime as dt
from logging import getLogger
from typing import Any

from services.api_servers.services import call_api_server_tool
from services.api_servers.types import ApiToolCall, ApiToolCallInputParams

from core.db.models.teams import TeamsMeeting
from core.db.session import async_session_maker
from sqlalchemy import func, update

logger = getLogger(__name__)

ACCOUNT_LOOKUP_TOOL = "accountLookup"


async def account_lookup(account_name: str, *, server: str | None = None) -> Any:
    if not account_name:
        raise ValueError("Account name is required.")
    if not server:
        raise ValueError("Salesforce API server is required.")

    api_call = ApiToolCall(
        server=server,
        tool=ACCOUNT_LOOKUP_TOOL,
        input_params=ApiToolCallInputParams(
            pathParams={
                "accountName": account_name,
                "account_name": account_name,
            },
            queryParams={"accountName": account_name},
        ),
    )
    result = await call_api_server_tool(api_call)

    if result.status_code >= 400:
        raise RuntimeError(
            f"Salesforce account lookup failed (status {result.status_code})."
        )

    try:
        return json.loads(result.content) if result.content else None
    except json.JSONDecodeError:
        logger.debug("Salesforce account lookup response was not JSON.")
        return result.content


async def post_stt_recording(
    payload: dict[str, Any],
    *,
    server: str | None = None,
    tool: str | None = None,
) -> Any:
    if not server:
        raise ValueError("Salesforce API server is required.")
    if not tool:
        raise ValueError("Salesforce STT recording tool is required.")
    api_call = ApiToolCall(
        server=server,
        tool=tool,
        input_params=ApiToolCallInputParams(requestBody=payload),
    )
    result = await call_api_server_tool(api_call)

    if result.status_code >= 400:
        error_body = result.content or ""
        raise RuntimeError(
            "Salesforce sttRecording failed "
            f"(status {result.status_code}): {error_body}"
        )

    try:
        return json.loads(result.content) if result.content else None
    except json.JSONDecodeError:
        logger.debug("Salesforce sttRecording response was not JSON.")
        return result.content


def config_requires_salesforce(settings: dict[str, Any] | None) -> bool:
    if not isinstance(settings, dict):
        return False
    salesforce_settings = (settings.get("integration") or {}).get("salesforce") or {}
    if not isinstance(salesforce_settings, dict):
        return False
    return bool(salesforce_settings.get("send_transcript_to_salesforce"))


def get_salesforce_api_server(settings: dict[str, Any] | None) -> str | None:
    if not isinstance(settings, dict):
        return None
    salesforce_settings = (settings.get("integration") or {}).get("salesforce") or {}
    if not isinstance(salesforce_settings, dict):
        return None
    value = str(salesforce_settings.get("salesforce_api_server") or "").strip()
    return value or None


def get_salesforce_stt_recording_tool(settings: dict[str, Any] | None) -> str | None:
    if not isinstance(settings, dict):
        return None
    salesforce_settings = (settings.get("integration") or {}).get("salesforce") or {}
    if not isinstance(salesforce_settings, dict):
        return None
    value = str(salesforce_settings.get("salesforce_stt_recording_tool") or "").strip()
    return value or None


def pick_first_account_id_and_name(
    result: Any, *, fallback_account_name: str
) -> tuple[str | None, str]:
    if not isinstance(result, list) or not result:
        return None, fallback_account_name

    first = result[0] if isinstance(result[0], dict) else {}
    account_id = first.get("accountId") if isinstance(first, dict) else None
    account_name_value = None
    if isinstance(first, dict):
        account_name_value = (
            first.get("accountName") or first.get("name") or first.get("Name")
        )
    if not account_name_value:
        account_name_value = fallback_account_name

    return account_id, str(account_name_value)


async def update_meeting_salesforce_account(
    *,
    chat_id: str,
    bot_id: str,
    account_id: str,
    account_name: str,
) -> int:
    now = dt.datetime.now(dt.timezone.utc)
    stmt = (
        update(TeamsMeeting)
        .where(TeamsMeeting.chat_id == chat_id, TeamsMeeting.bot_id == bot_id)
        .values(
            account_id=account_id,
            account_name=account_name,
            last_seen_at=now,
            updated_at=func.now(),
        )
    )

    async with async_session_maker() as session:
        try:
            result = await session.execute(stmt)
            await session.commit()
        except Exception:
            await session.rollback()
            raise

    return int(getattr(result, "rowcount", 0) or 0)


async def send_stt_recording_to_salesforce(
    *,
    context: Any,
    settings: dict[str, Any],
    job_id: str | None,
    conversation_date: str | None,
    source_file_name: str,
    source_file_type: str,
    account_id: str | None,
    send_expandable_section: Any,
) -> None:
    if not job_id:
        return

    if not config_requires_salesforce(settings):
        await context.send_activity(
            "Salesforce sync skipped: sending transcripts to Salesforce is disabled in settings."
        )
        return

    if not account_id:
        await context.send_activity(
            "Salesforce sync skipped: account id is not set for this meeting."
        )
        return

    if not conversation_date:
        conversation_date = dt.datetime.now(dt.timezone.utc).date().isoformat()

    salesforce_api_server = get_salesforce_api_server(settings)
    salesforce_stt_recording_tool = get_salesforce_stt_recording_tool(settings)
    if not salesforce_api_server or not salesforce_stt_recording_tool:
        await context.send_activity(
            "Salesforce sync skipped: API server or STT recording tool is not configured in settings."
        )
        return

    payload = {
        "external_job_id": job_id,
        "conversation_date": conversation_date,
        "source_file_name": source_file_name,
        "source_file_type": source_file_type,
        "account_id": account_id,
    }

    payload_json = json.dumps(payload, indent=2, ensure_ascii=True)
    await send_expandable_section(
        context,
        title="Salesforce payload sent.",
        content=payload_json,
        preserve_newlines=True,
    )

    try:
        result = await post_stt_recording(
            payload,
            server=salesforce_api_server,
            tool=salesforce_stt_recording_tool,
        )
    except Exception as err:
        logger.exception("Salesforce sttRecording failed for job %s", job_id)
        await send_expandable_section(
            context,
            title="Salesforce response: failed.",
            content=getattr(err, "message", str(err)),
            preserve_newlines=True,
        )
        return

    if isinstance(result, (dict, list)):
        response_json = json.dumps(result, indent=2, ensure_ascii=True)
        await send_expandable_section(
            context,
            title="Salesforce response: success.",
            content=response_json,
            preserve_newlines=True,
        )
        return

    await send_expandable_section(
        context,
        title="Salesforce response: success.",
        content=str(result),
        preserve_newlines=True,
    )


__all__ = [
    "account_lookup",
    "post_stt_recording",
    "config_requires_salesforce",
    "get_salesforce_api_server",
    "get_salesforce_stt_recording_tool",
    "pick_first_account_id_and_name",
    "update_meeting_salesforce_account",
    "send_stt_recording_to_salesforce",
]
