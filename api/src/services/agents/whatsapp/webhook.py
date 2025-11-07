import asyncio
import hashlib
import json
import os
import secrets
import httpx
from logging import getLogger
from typing import Any, Dict


from .runtime import WhatsappRuntime


logger = getLogger(__name__)


def _parse_env_int(name: str, default: int, *, minimum: int = 0, maximum: int | None = None) -> int:
    raw = os.environ.get(name)
    if raw is None:
        value = default
    else:
        try:
            value = int(raw)
        except ValueError:
            value = default
    if value < minimum:
        value = minimum
    if maximum is not None and value > maximum:
        value = maximum
    return value


def _parse_env_float(name: str, default: float, *, minimum: float = 0.0) -> float:
    raw = os.environ.get(name)
    if raw is None:
        value = default
    else:
        try:
            value = float(raw)
        except ValueError:
            value = default
    if value < minimum:
        value = minimum
    return value


WHATSAPP_GRAPH_VERSION = (os.environ.get("WHATSAPP_GRAPH_VERSION", "v24.0") or "v24.0").strip() or "v24.0"
_WHATSAPP_GRAPH_BASE_URL = f"https://graph.facebook.com/{WHATSAPP_GRAPH_VERSION}"
_DEFAULT_REPLY_DELAY_MS = 20_000
WHATSAPP_REPLY_DELAY_SECONDS = _parse_env_int(
    "WHATSAPP_REPLY_DELAY_MS",
    _DEFAULT_REPLY_DELAY_MS,
    minimum=0,
    maximum=24_000,
) / 1000.0
WHATSAPP_HTTP_TIMEOUT_SECONDS = _parse_env_float("WHATSAPP_HTTP_TIMEOUT_SECONDS", 10.0, minimum=0.1)


def _whatsapp_messages_url(runtime: WhatsappRuntime) -> str:
    return f"{_WHATSAPP_GRAPH_BASE_URL}/{runtime.phone_number_id}/messages"


def _whatsapp_headers(runtime: WhatsappRuntime) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {runtime.token}",
        "Content-Type": "application/json",
    }


def _extract_httpx_error_details(response: httpx.Response) -> str:
    try:
        data = response.json()
        return json.dumps(data)
    except json.JSONDecodeError:
        return response.text


async def _post_whatsapp_message(
    client: httpx.AsyncClient,
    runtime: WhatsappRuntime,
    payload: Dict[str, Any],
    *,
    operation: str,
    swallow_errors: bool = False,
) -> Dict[str, Any] | None:
    url = _whatsapp_messages_url(runtime)
    try:
        response = await client.post(url, json=payload, headers=_whatsapp_headers(runtime))
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        details = _extract_httpx_error_details(exc.response)
        logger.warning(
            "WhatsApp %s failed (status=%s): %s",
            operation,
            exc.response.status_code,
            details,
        )
        if swallow_errors:
            return None
        raise
    except httpx.RequestError as exc:
        logger.warning("WhatsApp %s request error: %s", operation, exc)
        if swallow_errors:
            return None
        raise


async def _mark_whatsapp_message_as_read(
    client: httpx.AsyncClient,
    runtime: WhatsappRuntime,
    message_id: str,
) -> None:
    await _post_whatsapp_message(
        client,
        runtime,
        {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        },
        operation=f"mark message {message_id} as read",
        swallow_errors=True,
    )


async def _send_whatsapp_typing_indicator(
    client: httpx.AsyncClient,
    runtime: WhatsappRuntime,
    message_id: str,
) -> None:
    await _post_whatsapp_message(
        client,
        runtime,
        {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
            "typing_indicator": {"type": "text"},
        },
        operation=f"send typing indicator for message {message_id}",
        swallow_errors=True,
    )


async def _send_whatsapp_text_message(
    client: httpx.AsyncClient,
    runtime: WhatsappRuntime,
    recipient: str,
    body: str,
) -> None:
    data = await _post_whatsapp_message(
        client,
        runtime,
        {
            "messaging_product": "whatsapp",
            "to": recipient,
            "text": {"body": body},
        },
        operation=f"send text message to {recipient}",
    )
    if data:
        sent_message_id = (data.get("messages") or [{}])[0].get("id")
        logger.info(
            "Sent WhatsApp text reply to %s: message_id=%s",
            recipient,
            sent_message_id,
        )


def _build_interactive_buttons_payload(body: str, inbound_message_id: str | None) -> Dict[str, Any]:
    hash_input = inbound_message_id or secrets.token_hex(8)
    hash_suffix = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()[:16]

    return {
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body},
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": f"like_{hash_suffix}",
                            "title": "👍Like",
                        },
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": f"dislike_{hash_suffix}",
                            "title": "👎Dislike",
                        },
                    },
                ]
            },
        },
    }


async def _send_whatsapp_buttons_message(
    client: httpx.AsyncClient,
    runtime: WhatsappRuntime,
    recipient: str,
    body: str,
    inbound_message_id: str | None,
) -> None:
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient,
    }
    payload.update(_build_interactive_buttons_payload(body, inbound_message_id))

    data = await _post_whatsapp_message(
        client,
        runtime,
        payload,
        operation=f"send interactive message to {recipient}",
    )
    if data:
        sent_message_id = (data.get("messages") or [{}])[0].get("id")
        logger.info(
            "Sent WhatsApp interactive reply to %s: message_id=%s source_message_id=%s",
            recipient,
            sent_message_id,
            inbound_message_id,
        )


async def _handle_whatsapp_interactive_reply(
    client: httpx.AsyncClient,
    runtime: WhatsappRuntime,
    message: Dict[str, Any],
) -> None:
    interactive = message.get("interactive") or {}
    interactive_type = interactive.get("type")
    from_number = message.get("from")
    reply_context_id = (message.get("context") or {}).get("id")

    if reply_context_id and reply_context_id in runtime.handled_interactive_message_ids:
        logger.info("Duplicate interactive reply ignored for message %s", reply_context_id)
        return

    if interactive_type == "button_reply":
        button_reply = interactive.get("button_reply") or {}
        button_id = button_reply.get("id", "")
        button_title = button_reply.get("title", "")

        if reply_context_id:
            runtime.handled_interactive_message_ids.add(reply_context_id)

        logger.info(
            "Button reply from %s: %s (%s) for message %s",
            from_number,
            button_title,
            button_id,
            reply_context_id,
        )

        if not from_number:
            return

        if button_id.startswith("like_"):
            acknowledgement = "Thanks for the Like! I've disabled further voting on this message."
        elif button_id.startswith("dislike_"):
            acknowledgement = "Dislike recorded. You will not be able to vote again on this message."
        else:
            acknowledgement = f"Noted your response: {button_title}."

        await _send_whatsapp_text_message(client, runtime, from_number, acknowledgement)
        return

    if interactive_type == "list_reply":
        list_reply = interactive.get("list_reply") or {}
        logger.info(
            "List reply from %s: %s (%s) for message %s",
            from_number,
            list_reply.get("title"),
            list_reply.get("id"),
            reply_context_id,
        )
        if reply_context_id:
            runtime.handled_interactive_message_ids.add(reply_context_id)
        return

    logger.info("Unhandled interactive message type: %s", interactive_type)


async def _handle_whatsapp_text_message(
    client: httpx.AsyncClient,
    runtime: WhatsappRuntime,
    message: Dict[str, Any],
    *,
    reply_delay_seconds: float,
) -> None:
    from_number = message.get("from")
    message_id = message.get("id")
    text_body = ((message.get("text") or {}).get("body") or "").strip()

    if not from_number or not message_id or not text_body:
        logger.warning("Skipping WhatsApp text message with missing data: from=%s id=%s", from_number, message_id)
        return

    reply_text = f'You said "{text_body}". Check https://www.google.com for more information.'

    await _mark_whatsapp_message_as_read(client, runtime, message_id)

    if reply_delay_seconds > 0:
        await _send_whatsapp_typing_indicator(client, runtime, message_id)
        await asyncio.sleep(reply_delay_seconds)

    await _send_whatsapp_buttons_message(client, runtime, from_number, reply_text, message_id)


async def _process_whatsapp_change(
    client: httpx.AsyncClient,
    runtime: WhatsappRuntime,
    change: Dict[str, Any],
    *,
    reply_delay_seconds: float,
) -> None:
    if change.get("field") != "messages":
        return

    value = change.get("value") or {}
    metadata_phone_number_id = ((value.get("metadata") or {}).get("phone_number_id") or "").strip()
    if metadata_phone_number_id and metadata_phone_number_id != runtime.phone_number_id:
        logger.warning(
            "Skipping WhatsApp message for unexpected phone_number_id=%s (expected %s)",
            metadata_phone_number_id,
            runtime.phone_number_id,
        )
        return

    statuses = value.get("statuses") or []
    for status in statuses:
        logger.info(
            "WhatsApp status update id=%s status=%s",
            status.get("id"),
            status.get("status"),
        )

    messages = value.get("messages") or []
    for message in messages:
        message_type = message.get("type")
        if message_type == "text":
            await _handle_whatsapp_text_message(
                client,
                runtime,
                message,
                reply_delay_seconds=reply_delay_seconds,
            )
        elif message_type == "interactive":
            message_id = message.get("id")
            if message_id:
                await _mark_whatsapp_message_as_read(client, runtime, message_id)
            await _handle_whatsapp_interactive_reply(client, runtime, message)
        else:
            logger.info("Ignoring WhatsApp message type: %s", message_type)


async def process_whatsapp_webhook_payload(
    payload: Dict[str, Any],
    runtime: WhatsappRuntime,
    *,
    reply_delay_seconds: float | None = None,
) -> None:
    if not isinstance(payload, dict):
        return

    effective_delay = WHATSAPP_REPLY_DELAY_SECONDS if reply_delay_seconds is None else max(reply_delay_seconds, 0.0)

    try:
        async with httpx.AsyncClient(timeout=WHATSAPP_HTTP_TIMEOUT_SECONDS) as client:
            entries = payload.get("entry") or []
            for entry in entries:
                changes = entry.get("changes") or []
                for change in changes:
                    await _process_whatsapp_change(
                        client,
                        runtime,
                        change,
                        reply_delay_seconds=effective_delay,
                    )
    except Exception:
        logger.exception(
            "Failed to process WhatsApp webhook payload for phone_number_id=%s",
            runtime.phone_number_id,
        )


__all__ = ["process_whatsapp_webhook_payload"]

