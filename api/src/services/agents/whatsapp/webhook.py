import hashlib
import json
import secrets
from logging import getLogger
from typing import Any, Dict

import httpx

from services.agents.conversations import get_conversation, set_message_feedback
from services.agents.utils.conversation_helpers import (
    AssistantPayload,
    WELCOME_LEARN_MORE_URL,
    close_conversation,
    continue_conversation,
    handle_action_confirmation,
    get_conversation_info,
)
from services.agents.models import (
    AgentConversationMessageRole,
    AgentConversationWithMessagesPublic,
)
from services.agents.utils.markdown import to_whatsapp_markdown
from services.common.models import (
    LlmResponseFeedback,
    LlmResponseFeedbackReason,
    LlmResponseFeedbackType,
)
from services.observability.utils import observability_overrides
from stores import RecordNotFoundError

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

    formatted_text = to_whatsapp_markdown(base_text).strip()
    if len(formatted_text) > 1024:
        formatted_text = formatted_text[:1021].rstrip() + "..."

    return formatted_text or "I don't have anything to share yet, but I'm here to help!"


def _build_confirmation_prompt(
    payload: AssistantPayload,
    *,
    agent_system_name: str,
) -> tuple[str, dict[str, Any], list[dict[str, str]], list[str]]:
    action_requests = payload.get("action_requests") or []
    if not action_requests:
        action_requests = [{}]

    multiple = len(action_requests) > 1
    confirmation_messages: list[str] = []
    request_ids: list[str] = []

    for index, request in enumerate(action_requests, start=1):
        message = ""
        request_id = None
        if isinstance(request, dict):
            message = request.get("action_message") or ""
            request_id = request.get("id")
        if not message:
            message = "The assistant requested an action."
        if multiple:
            message = f"{index}. {message}"
        confirmation_messages.append(message)
        if request_id:
            request_ids.append(str(request_id))

    header_text = "AI Assistant Requires Confirmation"

    text_sections = [f"*{header_text}*"]
    text_sections.extend(confirmation_messages)
    text_sections.append("Tap Confirm to proceed or Reject to cancel.")
    text_sections.append(f"Agent: {agent_system_name}")

    formatted_text = to_whatsapp_markdown("\n\n".join(text_sections)).strip()
    if len(formatted_text) > 1024:
        formatted_text = formatted_text[:1021].rstrip() + "..."

    confirmation_card = {
        "header": header_text,
        "messages": confirmation_messages,
    }

    buttons = [
        {"id": "confirm", "title": "✅ Confirm"},
        {"id": "reject", "title": "✋ Reject"},
    ]

    return formatted_text or header_text, confirmation_card, buttons, request_ids


async def _deliver_assistant_payload(
    client: httpx.AsyncClient,
    runtime: WhatsappRuntime,
    recipient: str,
    payload: AssistantPayload | None,
    reply_source_id: str | None,
    *,
    user_id: str | None,
) -> None:
    if not payload:
        logger.info(
            "No assistant payload to deliver for WhatsApp recipient=%s", recipient
        )
        return

    conversation_id = payload.get("conversation_id")
    agent_message_id = payload.get("message_id")
    trace_id = payload.get("trace_id")
    agent_system_name = payload.get("agent_system_name") or runtime.agent_system_name

    action_requests = payload.get("action_requests") or []
    requires_confirmation = bool(
        payload.get("requires_confirmation") and action_requests
    )

    if requires_confirmation:
        confirmation_text, confirmation_card, buttons, request_ids = (
            _build_confirmation_prompt(payload, agent_system_name=agent_system_name)
        )
        if request_ids:
            context_payload = {
                "type": "action_confirmation",
                "conversation_id": conversation_id,
                "message_id": agent_message_id or reply_source_id,
                "request_ids": request_ids,
                "user_id": user_id,
                "trace_id": trace_id,
                "agent_system_name": agent_system_name,
                "confirmation_card": confirmation_card,
            }
            await _send_whatsapp_buttons_message(
                client,
                runtime,
                recipient,
                confirmation_text,
                reply_source_id,
                buttons=buttons,
                context=context_payload,
            )
            return

    reply_text = _prepare_reply_text(payload)
    buttons = [
        {"id": "like", "title": "👍Like"},
        {"id": "dislike", "title": "👎Dislike"},
    ]
    context_payload = {
        "type": "feedback",
        "conversation_id": conversation_id,
        "message_id": agent_message_id,
    }
    await _send_whatsapp_buttons_message(
        client,
        runtime,
        recipient,
        reply_text,
        reply_source_id,
        buttons=buttons,
        context=context_payload,
    )


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
        response = await client.post(
            url, json=payload, headers=_whatsapp_headers(runtime)
        )
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


def _build_interactive_buttons_payload(
    body: str,
    inbound_message_id: str | None,
    buttons: list[dict[str, str]],
) -> Dict[str, Any]:
    hash_input = inbound_message_id or secrets.token_hex(8)
    hash_suffix = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()[:16]

    button_entries: list[Dict[str, Any]] = []
    for button in buttons:
        button_id_prefix = (button.get("id") or secrets.token_hex(4)).strip()
        button_title = (button.get("title") or "Select").strip()
        button_id = f"{button_id_prefix}_{hash_suffix}"
        button_entries.append(
            {
                "type": "reply",
                "reply": {
                    "id": button_id,
                    "title": button_title[:24],
                },
            }
        )

    return {
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body},
            "action": {"buttons": button_entries[:3]},
        },
    }


async def _send_whatsapp_buttons_message(
    client: httpx.AsyncClient,
    runtime: WhatsappRuntime,
    recipient: str,
    body: str,
    inbound_message_id: str | None,
    *,
    buttons: list[dict[str, str]],
    context: dict | None = None,
) -> None:
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient,
    }
    payload.update(
        _build_interactive_buttons_payload(body, inbound_message_id, buttons)
    )

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
        if sent_message_id and context:
            runtime.interactive_context[sent_message_id] = context
            if len(runtime.interactive_context) > 500:
                oldest_key = next(iter(runtime.interactive_context))
                runtime.interactive_context.pop(oldest_key, None)


def _normalize_id(value: Any) -> str | None:
    if value is None:
        return None
    try:
        return str(value)
    except Exception:
        return None


async def _load_conversation(
    conversation_id: str,
) -> AgentConversationWithMessagesPublic | None:
    if not conversation_id:
        return None
    try:
        return await get_conversation(conversation_id)
    except RecordNotFoundError:
        logger.warning(
            "Conversation %s not found while checking WhatsApp interaction state",
            conversation_id,
        )
    except Exception:
        logger.exception(
            "Failed to load conversation %s while checking WhatsApp interaction state",
            conversation_id,
        )
    return None


def _extract_feedback_type(feedback: Any) -> str | None:
    if feedback is None:
        return None
    value = getattr(feedback, "type", None)
    if value is None and isinstance(feedback, dict):
        value = feedback.get("type")
    return str(value) if value is not None else None


def _get_message_feedback(
    conversation: AgentConversationWithMessagesPublic | None,
    message_id: str,
) -> str | None:
    if not conversation:
        return None
    target_id = _normalize_id(message_id)
    if not target_id:
        return None
    for message in conversation.messages or []:
        if _normalize_id(getattr(message, "id", None)) == target_id:
            return _extract_feedback_type(getattr(message, "feedback", None))
    return None


def _get_existing_confirmations(
    conversation: AgentConversationWithMessagesPublic | None,
    request_ids: list[str],
) -> dict[str, bool]:
    if not conversation or not request_ids:
        return {}
    wanted_ids = {_normalize_id(request_id) for request_id in request_ids if request_id}
    if not wanted_ids:
        return {}
    results: dict[str, bool] = {}
    for message in conversation.messages or []:
        if getattr(message, "role", None) != AgentConversationMessageRole.USER:
            continue
        confirmations = getattr(message, "action_call_confirmations", None) or []
        for confirmation in confirmations:
            request_id = _normalize_id(getattr(confirmation, "request_id", None))
            if request_id and request_id in wanted_ids and request_id not in results:
                results[request_id] = bool(getattr(confirmation, "confirmed", False))
    return results


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
        logger.info(
            "Duplicate interactive reply ignored for message %s", reply_context_id
        )
        return

    stored_context: dict[str, Any] | None = None
    if reply_context_id:
        stored_context = runtime.interactive_context.pop(reply_context_id, None)
        if stored_context is None:
            logger.warning(
                "No interactive context found for WhatsApp reply message_id=%s",
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

        context_type = (stored_context or {}).get("type") or "feedback"

        if context_type == "action_confirmation":
            conversation_id = (stored_context or {}).get("conversation_id")
            request_ids = (stored_context or {}).get("request_ids") or []
            user_id = (stored_context or {}).get("user_id")
            trace_id = (stored_context or {}).get("trace_id")
            agent_name = (stored_context or {}).get(
                "agent_system_name"
            ) or runtime.agent_system_name
            message_id = (stored_context or {}).get("message_id") or reply_context_id

            if not (conversation_id and request_ids and user_id):
                logger.warning(
                    "Missing confirmation context for WhatsApp reply (conversation=%s, request_ids=%s, user_id=%s)",
                    conversation_id,
                    request_ids,
                    user_id,
                )
                await _send_whatsapp_text_message(
                    client,
                    runtime,
                    from_number,
                    "Sorry, I couldn't process that confirmation. Please try again.",
                )
                return

            confirmed = button_id.startswith("confirm_")
            conversation = await _load_conversation(conversation_id)
            existing_confirmations = _get_existing_confirmations(
                conversation, request_ids
            )

            if existing_confirmations:
                if all(value == confirmed for value in existing_confirmations.values()):
                    acknowledgement = (
                        "You've already confirmed this action earlier."
                        if confirmed
                        else "You've already rejected this action earlier."
                    )
                else:
                    acknowledgement = "This action was already handled earlier, so I can't change that decision."
                await _send_whatsapp_text_message(
                    client, runtime, from_number, acknowledgement
                )
                return

            acknowledgement = (
                "Thanks! I'll proceed with the requested action."
                if confirmed
                else "No problem, I won't run that action."
            )

            try:
                assistant_payload = await handle_action_confirmation(
                    agent_system_name=agent_name,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    request_ids=[str(item) for item in request_ids],
                    confirmed=confirmed,
                    **observability_overrides(
                        trace_id=trace_id, consumer_name="WhatsApp"
                    ),
                )
            except Exception:
                logger.exception(
                    "Failed to process WhatsApp action confirmation (conversation=%s user=%s)",
                    conversation_id,
                    user_id,
                )
                await _send_whatsapp_text_message(
                    client,
                    runtime,
                    from_number,
                    "Sorry, something went wrong while processing your confirmation.",
                )
                return

            await _send_whatsapp_text_message(
                client, runtime, from_number, acknowledgement
            )

            if assistant_payload:
                reply_source_id = assistant_payload.get("message_id") or message_id
                await _deliver_assistant_payload(
                    client,
                    runtime,
                    from_number,
                    assistant_payload,
                    reply_source_id,
                    user_id=user_id,
                )
            return

        context_conversation_id = (stored_context or {}).get("conversation_id")
        context_message_id = (stored_context or {}).get("message_id")

        if button_id.startswith("like_"):
            acknowledgement = (
                "Thanks for the Like! I've disabled further voting on this message."
            )
            if context_conversation_id and context_message_id:
                try:
                    conversation = await _load_conversation(context_conversation_id)
                    existing_feedback_type = _get_message_feedback(
                        conversation, context_message_id
                    )
                    if existing_feedback_type:
                        if existing_feedback_type == LlmResponseFeedbackType.LIKE:
                            acknowledgement = "You've already liked this message. Thanks for the feedback!"
                        elif existing_feedback_type == LlmResponseFeedbackType.DISLIKE:
                            acknowledgement = "This message was already disliked, so you can't like it now."
                        await _send_whatsapp_text_message(
                            client, runtime, from_number, acknowledgement
                        )
                        return
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
            acknowledgement = (
                "Dislike recorded. You will not be able to vote again on this message."
            )
            if context_conversation_id and context_message_id:
                try:
                    conversation = await _load_conversation(context_conversation_id)
                    existing_feedback_type = _get_message_feedback(
                        conversation, context_message_id
                    )
                    if existing_feedback_type:
                        if existing_feedback_type == LlmResponseFeedbackType.DISLIKE:
                            acknowledgement = "You've already disliked this message. Thanks for the feedback!"
                        elif existing_feedback_type == LlmResponseFeedbackType.LIKE:
                            acknowledgement = "This message was already liked, so you can't dislike it now."
                        await _send_whatsapp_text_message(
                            client, runtime, from_number, acknowledgement
                        )
                        return
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


def _build_whatsapp_welcome_text(agent_system_name: str) -> str:
    return (
        "👋 Welcome aboard!\n\n"
        "I'm your assistant for "
        f"**{agent_system_name or 'Magnet AI'}**.\n\n"
        "• Ask me a question and I'll pass it to the Magnet AI Agent and deliver the response back to WhatsApp.\n"
        f"• Learn more: {WELCOME_LEARN_MORE_URL}"
    )


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
        logger.warning(
            "Skipping WhatsApp text message with missing data: from=%s id=%s",
            from_number,
            message_id,
        )
        return

    lower_text = text_body.lower()
    if lower_text in {"/welcome", "welcome", "/start", "start"}:
        await _mark_whatsapp_message_as_read(client, runtime, message_id)
        welcome_text = _build_whatsapp_welcome_text(runtime.agent_system_name)
        await _send_whatsapp_text_message(client, runtime, from_number, welcome_text)
        return

    if not user_id:
        logger.warning(
            "WhatsApp payload missing contacts[].wa_id; falling back to sender number %s",
            from_number,
        )
    resolved_user_id = user_id or from_number

    if lower_text in {"/close", "close", "/restart", "restart"}:
        await _mark_whatsapp_message_as_read(client, runtime, message_id)
        result = await close_conversation(runtime.agent_system_name, resolved_user_id)
        await _send_whatsapp_text_message(client, runtime, from_number, result)
        return

    if lower_text in {"/get_conversation_info", "get_conversation_info"}:
        await _mark_whatsapp_message_as_read(client, runtime, message_id)
        info = await get_conversation_info(runtime.agent_system_name, resolved_user_id)
        await _send_whatsapp_text_message(client, runtime, from_number, info)
        return

    await _mark_whatsapp_message_as_read(client, runtime, message_id)
    await _send_whatsapp_typing_indicator(client, runtime, message_id)

    assistant_payload: AssistantPayload | None = None
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
        await _send_whatsapp_text_message(
            client,
            runtime,
            from_number,
            "Sorry, I'm having trouble responding right now.",
        )
        return

    reply_source_id = (
        assistant_payload.get("message_id")
        or assistant_payload.get("conversation_id")
        or message_id
    )
    await _deliver_assistant_payload(
        client,
        runtime,
        from_number,
        assistant_payload,
        reply_source_id,
        user_id=resolved_user_id,
    )


async def _process_whatsapp_change(
    client: httpx.AsyncClient,
    runtime: WhatsappRuntime,
    change: Dict[str, Any],
) -> None:
    if change.get("field") != "messages":
        return

    value = change.get("value") or {}
    metadata_phone_number_id = (
        (value.get("metadata") or {}).get("phone_number_id") or ""
    ).strip()
    if metadata_phone_number_id and metadata_phone_number_id != runtime.phone_number_id:
        logger.warning(
            "Skipping WhatsApp message for unexpected phone_number_id=%s (expected %s)",
            metadata_phone_number_id,
            runtime.phone_number_id,
        )
        return

    user_id = _extract_contact_wa_id(value)
    logger.info("WhatsApp message received from user_id=%s", user_id)

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
