import hashlib
import json
import secrets
from logging import getLogger
from typing import Any, Dict

import httpx

from services.agents.conversations import set_message_feedback
from services.agents.utils.conversation_helpers import AssistantPayload, continue_conversation
from services.common.models import (
    LlmResponseFeedback,
    LlmResponseFeedbackReason,
    LlmResponseFeedbackType,
)

from .runtime import WhatsappRuntime


logger = getLogger(__name__)




WHATSAPP_GRAPH_VERSION = "v24.0"
_WHATSAPP_GRAPH_BASE_URL = f"https://graph.facebook.com/{WHATSAPP_GRAPH_VERSION}"
WHATSAPP_HTTP_TIMEOUT_SECONDS = 20.0


def _whatsapp_messages_url(runtime: WhatsappRuntime) -> str:
    return f"{_WHATSAPP_GRAPH_BASE_URL}/{runtime.phone_number_id}/messages"


def _whatsapp_headers(runtime: WhatsappRuntime) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {runtime.token}",
        "Content-Type": "application/json",
    }


def _extract_contact_wa_id(value: Dict[str, Any]) -> str | None:
    contacts = value.get("contacts") or []
    for contact in contacts:
        if not isinstance(contact, dict):
            continue
        wa_id = contact.get("wa_id")
        if isinstance(wa_id, str) and wa_id:
            return wa_id
    return None


def _extract_httpx_error_details(response: httpx.Response) -> str:
    try:
        data = response.json()
        return json.dumps(data)
    except json.JSONDecodeError:
        return response.text


def _stringify_assistant_content(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, dict):
        for key in ("text", "message", "content"):
            value = content.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return json.dumps(content, ensure_ascii=False)

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                if item.strip():
                    parts.append(item.strip())
            elif isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    parts.append(text.strip())
        if parts:
            return "\n\n".join(parts)
        return json.dumps(content, ensure_ascii=False)

    if content is None:
        return ""

    return str(content)


def _prepare_reply_text(payload: AssistantPayload | None) -> str:
    if not payload:
        return "Sorry, I'm having trouble responding right now."

    base_text = _stringify_assistant_content(payload.get("content"))
    if not base_text:
        base_text = "I'm still thinking about that. Could you rephrase your question?"

    if payload.get("requires_confirmation"):
        base_text = (
            f"{base_text}\n\nLet me know if you'd like to proceed by tapping 👍Like or decline with 👎Dislike."
        )

    base_text = base_text.strip()
    if len(base_text) > 1024:
        base_text = base_text[:1021].rstrip() + "..."

    return base_text or "I don't have anything to share yet, but I'm here to help!"


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
    *,
    conversation_id: str | None,
    agent_message_id: str | None,
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
        if (
            sent_message_id
            and conversation_id
            and agent_message_id
        ):
            runtime.feedback_context[sent_message_id] = (conversation_id, agent_message_id)
            if len(runtime.feedback_context) > 500:
                oldest_key = next(iter(runtime.feedback_context))
                runtime.feedback_context.pop(oldest_key, None)


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

    context_conversation_id: str | None = None
    context_message_id: str | None = None
    if reply_context_id:
        stored_context = runtime.feedback_context.pop(reply_context_id, None)
        if stored_context:
            context_conversation_id, context_message_id = stored_context
        else:
            logger.warning(
                "No feedback context found for WhatsApp interactive reply message_id=%s",
                reply_context_id,
            )

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
            if context_conversation_id and context_message_id:
                try:
                    feedback = LlmResponseFeedback(type=LlmResponseFeedbackType.LIKE)
                    await set_message_feedback(
                        conversation_id=context_conversation_id,
                        message_id=context_message_id,
                        data=feedback,
                        consumer_name="WhatsApp",
                    )
                except Exception:
                    logger.exception(
                        "Failed to record WhatsApp like feedback (conversation=%s, message=%s)",
                        context_conversation_id,
                        context_message_id,
                    )
            else:
                logger.warning(
                    "Unable to record WhatsApp like feedback (missing context)."
                )
        elif button_id.startswith("dislike_"):
            acknowledgement = "Dislike recorded. You will not be able to vote again on this message."
            if context_conversation_id and context_message_id:
                try:
                    feedback = LlmResponseFeedback(
                        type=LlmResponseFeedbackType.DISLIKE,
                        reason=LlmResponseFeedbackReason.OTHER,
                    )
                    await set_message_feedback(
                        conversation_id=context_conversation_id,
                        message_id=context_message_id,
                        data=feedback,
                        consumer_name="WhatsApp",
                    )
                except Exception:
                    logger.exception(
                        "Failed to record WhatsApp dislike feedback (conversation=%s, message=%s)",
                        context_conversation_id,
                        context_message_id,
                    )
            else:
                logger.warning(
                    "Unable to record WhatsApp dislike feedback (missing context)."
                )
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
    user_id: str | None,
) -> None:
    from_number = message.get("from")
    message_id = message.get("id")
    text_body = ((message.get("text") or {}).get("body") or "").strip()

    if not from_number or not message_id or not text_body:
        logger.warning("Skipping WhatsApp text message with missing data: from=%s id=%s", from_number, message_id)
        return

    if not user_id:
        logger.warning(
            "WhatsApp payload missing contacts[].wa_id; falling back to sender number %s",
            from_number,
        )
    resolved_user_id = user_id or from_number

    await _mark_whatsapp_message_as_read(client, runtime, message_id)
    await _send_whatsapp_typing_indicator(client, runtime, message_id)

    assistant_payload: AssistantPayload | None = None
    conversation_id: str | None = None
    assistant_message_id: str | None = None
    reply_source_id: str | None = None
    try:
        assistant_payload = await continue_conversation(
            agent_system_name=runtime.agent_system_name,
            user_id=resolved_user_id,
            text=text_body,
            consumer_name="WhatsApp",
        )
    except Exception:
        logger.exception(
            "Failed to continue conversation for WhatsApp user_id=%s agent=%s",
            resolved_user_id,
            runtime.agent_system_name,
        )
        reply_text = "Sorry, I'm having trouble responding right now."
    else:
        reply_text = _prepare_reply_text(assistant_payload)
        conversation_id = assistant_payload.get("conversation_id") if assistant_payload else None
        assistant_message_id = assistant_payload.get("message_id") if assistant_payload else None
        reply_source_id = assistant_message_id or conversation_id

    reply_source_id = reply_source_id or message_id
    await _send_whatsapp_buttons_message(
        client,
        runtime,
        from_number,
        reply_text,
        reply_source_id,
        conversation_id=conversation_id,
        agent_message_id=assistant_message_id,
    )


async def _process_whatsapp_change(
    client: httpx.AsyncClient,
    runtime: WhatsappRuntime,
    change: Dict[str, Any],
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

    user_id = _extract_contact_wa_id(value)

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
                user_id=user_id,
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
) -> None:
    if not isinstance(payload, dict):
        return

    try:
        async with httpx.AsyncClient(timeout=WHATSAPP_HTTP_TIMEOUT_SECONDS) as client:
            entries = payload.get("entry") or []
            for entry in entries:
                changes = entry.get("changes") or []
                for change in changes:
                    await _process_whatsapp_change(client, runtime, change)
    except Exception:
        logger.exception(
            "Failed to process WhatsApp webhook payload for phone_number_id=%s",
            runtime.phone_number_id,
        )


__all__ = ["process_whatsapp_webhook_payload"]

