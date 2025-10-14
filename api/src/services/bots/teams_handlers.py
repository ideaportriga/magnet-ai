
from typing import Any
from microsoft_agents.hosting.core import AgentApplication, TurnContext, TurnState
from microsoft_agents.activity import Attachment, Activity
from services.agents.conversations import (
    get_last_conversation_by_client_id,
    create_conversation,
    add_user_message,
    set_message_feedback,
)
from services.agents.models import AgentConversationMessageRole
from services.common.models import (
    LlmResponseFeedback,
    LlmResponseFeedbackType,
    LlmResponseFeedbackReason,
)
from .cards import create_welcome_card, create_magnet_response_card, create_feedback_result_card
from logging import getLogger


logger = getLogger(__name__)


async def _continue_conversation(agent_system_name: str, aad_object_id: str, text: str) -> dict[str, str | None]:
    """Continue or start an agent conversation and return the assistant's reply payload."""
    client_id = f"{aad_object_id}@{agent_system_name}"
    logger.info("[bots] _continue_conversation started: client_id=%s", client_id)

    def _payload(conversation_id: str, message: Any) -> dict[str, str | None]:
        return {
            "conversation_id": conversation_id,
            "message_id": (str(getattr(message, "id", "")) or None) if message else None,
            "content": getattr(message, "content", None) if message else None,
        }

    def _extract_assistant(resp: Any) -> Any:
        msg = getattr(resp, "assistant_message", None)
        if msg:
            return msg
        for m in (getattr(resp, "messages", []) or []):
            role = getattr(m, "role", None)
            if role == AgentConversationMessageRole.ASSISTANT or str(role).lower() == "assistant":
                return m
        return None

    try:
        last = await get_last_conversation_by_client_id(client_id)
    except Exception:
        logger.exception("[bots] failed to fetch last conversation for %s", client_id)
        return {}

    if not last:
        try:
            resp = await create_conversation(
                agent_system_name_or_config=agent_system_name,
                content=text,
                client_id=client_id,
            )
            conv_id = str(getattr(resp, "id", "")) or ""
            assistant = _extract_assistant(resp)
            logger.info("[bots] created conversation %s", conv_id)
            return _payload(conv_id, assistant)
        except Exception:
            logger.exception("[bots] create_conversation error for %s", client_id)
            return {}

    conv_id = str(getattr(last, "id", "")) or ""
    try:
        resp = await add_user_message(
            agent_system_name_or_config=agent_system_name,
            conversation_or_id=conv_id,
            user_message_content=text,
        )
        assistant = _extract_assistant(resp)
        logger.info("[bots] appended user message to %s", conv_id)
        return _payload(conv_id, assistant)
    except Exception:
        logger.exception("[bots] add_user_message error for conversation %s", conv_id)
        return {}
    

async def _send_welcome_card(ctx: TurnContext, agent_system_name: str):
    bot_name = getattr(getattr(getattr(ctx, "activity", None), "recipient", None), "name", None) or 'Magnet Agent'
    card = create_welcome_card(bot_name, agent_system_name)
    attachment = Attachment(
        content_type="application/vnd.microsoft.card.adaptive",
        content=card,
    )
    activity = Activity(type="message", attachments=[attachment])
    await ctx.send_activity(activity)


async def _send_response_card(ctx: TurnContext, payload):
    card = create_magnet_response_card(payload)
    attachment = Attachment(
        content_type="application/vnd.microsoft.card.adaptive",
        content=card,
    )
    activity = Activity(type="message", attachments=[attachment])
    await ctx.send_activity(activity)


async def _send_feedback_result_card(ctx: TurnContext, payload: dict):
    logger.info (f"[bots] _send_feedback_result_card payload: {payload}")
    card = create_feedback_result_card(payload)
    await ctx.send_activity(Activity(
        type="invokeResponse",
        value={
            "status": 200,
            "body": {
                "statusCode": 200,
                "type": "application/vnd.microsoft.card.adaptive",
                "value": card
            }
        }
    ))    


def _make_on_members_added_handler(agent_system_name: str):
    async def on_members_added(ctx: TurnContext, _state: TurnState) -> None:
        await _send_welcome_card(ctx, agent_system_name)

    return on_members_added


def _make_on_message_handler(agent_system_name: str, app: AgentApplication[TurnState]):
    async def on_message(ctx: TurnContext, _state: TurnState) -> None:
        text = (getattr(getattr(ctx, "activity", None), "text", None) or "").strip()
        if not text:
            logger.debug("[bots] on_message: empty text; ignoring")
            return

        if text.lower() in {"/welcome", "/start"}:
            await _send_welcome_card(ctx, agent_system_name)
            return

        await app.typing.start(ctx)

        aad_object_id = getattr(
            getattr(getattr(ctx, "activity", None), "from_property", None),
            "aad_object_id",
            None,
        )
        if not aad_object_id:
            logger.error("[bots] on_message: missing aad_object_id in activity.from_property")
            await ctx.send_activity("Sorry, I couldn't identify you. Please try again.")
            return

        try:
            assistant_payload: dict[str, Any] = await _continue_conversation(
                agent_system_name, aad_object_id, text
            )
            logger.info("[bots] on_message assistant_payload: %s", assistant_payload)
        except Exception:
            logger.exception("[bots] on_message: _continue_conversation failed")
            await ctx.send_activity("Sorry, I couldn't process your message.")
            return

        if assistant_payload and (assistant_payload.get("content") or assistant_payload.get("message_id")):
            await _send_response_card(ctx, assistant_payload)
        else:
            logger.warning("[bots] on_message: empty assistant payload for aad=%s", aad_object_id)
            await ctx.send_activity("Hmm, I didn't get a reply")

    return on_message


async def on_invoke_feedback(ctx: TurnContext, _state: TurnState) -> None:
    value: dict[str, Any] = getattr(ctx.activity, "value", {}) or {}
    action: dict[str, Any] = (value.get("action") or value) or {}
    verb = str(action.get("verb") or "").lower()

    if verb not in {"like", "dislike"}:
        logger.warning("[bots] unexpected feedback verb: %s", verb)
        return

    data: dict[str, Any] = action.get("data") or {}
    conversation_id = str(data.get("conversation_id") or "")
    message_id = str(data.get("message_id") or "")
    text = data.get("text") or None

    if not conversation_id or not message_id:
        logger.error("[bots] missing IDs: conversation_id=%s, message_id=%s", conversation_id, message_id)
        await ctx.send_activity("Sorry, feedback cannot be recorded (missing IDs).")
        return

    try:
        if verb == "like":
            feedback = LlmResponseFeedback(type=LlmResponseFeedbackType.LIKE)
            await set_message_feedback(conversation_id=conversation_id, message_id=message_id, data=feedback)
            await _send_feedback_result_card(ctx, {
                "conversation_id": conversation_id,
                "text": text,
                "reaction": "like",
            })
        else:  # dislike
            reason = str(data.get("dislike_reason") or "other").lower()
            try:
                if reason == "other":
                    reason = LlmResponseFeedbackReason.OTHER
                else:
                    reason = LlmResponseFeedbackReason(reason)
            except Exception:
                reason = LlmResponseFeedbackReason.OTHER

            comment = data.get("dislike_comment") or None
            feedback = LlmResponseFeedback(
                type=LlmResponseFeedbackType.DISLIKE,
                reason=reason,
                comment=comment,
            )
            await set_message_feedback(conversation_id=conversation_id, message_id=message_id, data=feedback)
            await _send_feedback_result_card(ctx, {
                "conversation_id": conversation_id,
                "text": text,
                "reaction": "dislike",
                "reason": reason.value,
                "comment": comment,
            })
    except Exception:
        logger.exception("[bots] invoke feedback error (conv=%s, msg=%s)", conversation_id, message_id)
        await ctx.send_activity("Sorry, failed to record your feedback.")


def register_handlers(app: AgentApplication[TurnState], *, agent_system_name: str | None = None) -> None:
    """Register the activity handlers on the provided application."""

    app.conversation_update("membersAdded")(_make_on_members_added_handler(agent_system_name or ""))
    app.activity("message")(_make_on_message_handler(agent_system_name or "", app))
    app.activity("invoke")(on_invoke_feedback)
