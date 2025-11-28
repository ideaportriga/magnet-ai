from typing import Any
from microsoft_agents.hosting.core import AgentApplication, TurnContext, TurnState
from microsoft_agents.activity import Attachment, Activity
from services.agents.conversations import set_message_feedback
from services.common.models import (
    LlmResponseFeedback,
    LlmResponseFeedbackType,
    LlmResponseFeedbackReason,
)
from .cards import (
    create_welcome_card,
    create_magnet_response_card,
    create_feedback_result_card,
    create_confirmation_result_card,
)
from services.agents.utils.conversation_helpers import (
    AssistantPayload,
    continue_conversation,
    handle_action_confirmation,
    get_conversation_info,
    close_conversation,
    close_conversation_by_id,
    DEFAULT_AGENT_DISPLAY_NAME,
)
from services.observability.utils import observability_overrides
from logging import getLogger


logger = getLogger(__name__)


async def _send_welcome_card(ctx: TurnContext, agent_system_name: str):
    bot_name = (
        getattr(
            getattr(getattr(ctx, "activity", None), "recipient", None), "name", None
        )
        or DEFAULT_AGENT_DISPLAY_NAME
    )
    card = create_welcome_card(bot_name, agent_system_name)
    attachment = Attachment(
        content_type="application/vnd.microsoft.card.adaptive",
        content=card,
    )
    activity = Activity(type="message", attachments=[attachment])
    await ctx.send_activity(activity)


async def _send_response_card(ctx: TurnContext, payload: AssistantPayload) -> None:
    card = create_magnet_response_card(payload)
    attachment = Attachment(
        content_type="application/vnd.microsoft.card.adaptive",
        content=card,
    )
    activity = Activity(type="message", attachments=[attachment])
    await ctx.send_activity(activity)


async def _send_feedback_result_card(ctx: TurnContext, payload: dict):
    logger.info(f"[agents] _send_feedback_result_card payload: {payload}")
    card = create_feedback_result_card(payload)
    await ctx.send_activity(
        Activity(
            type="invokeResponse",
            value={
                "status": 200,
                "body": {
                    "statusCode": 200,
                    "type": "application/vnd.microsoft.card.adaptive",
                    "value": card,
                },
            },
        )
    )


def _make_on_members_added_handler(agent_system_name: str):
    async def on_members_added(ctx: TurnContext, _state: TurnState) -> None:
        await _send_welcome_card(ctx, agent_system_name)

    return on_members_added


def _make_on_message_handler(agent_system_name: str, app: AgentApplication[TurnState]):
    def _format_exception_message(e: Exception) -> str:
        etype = e.__class__.__name__
        message = str(e)
        return f"{etype}: {message}" if message else etype

    async def on_message(ctx: TurnContext, _state: TurnState) -> None:
        text = (getattr(getattr(ctx, "activity", None), "text", None) or "").strip()
        if not text:
            logger.debug("[agents] on_message: empty text; ignoring")
            return

        if text.strip().lower() in {"/welcome", "/start"}:
            await _send_welcome_card(ctx, agent_system_name)
            return

        aad_object_id = getattr(
            getattr(getattr(ctx, "activity", None), "from_property", None),
            "aad_object_id",
            None,
        )
        if not aad_object_id:
            logger.error(
                "[agents] on_message: missing aad_object_id in activity.from_property"
            )
            await ctx.send_activity("Sorry, I couldn't identify you. Please try again.")
            return

        if text.strip().lower() in {"/close", "/restart"}:
            res = await close_conversation(agent_system_name, aad_object_id)
            await ctx.send_activity(res)
            return

        if text.strip().lower() in {"/get_conversation_info"}:
            res = await get_conversation_info(agent_system_name, aad_object_id)
            await ctx.send_activity(res)
            return

        try:
            await app.typing.start(ctx)

            assistant_payload: AssistantPayload = await continue_conversation(
                agent_system_name=agent_system_name,
                user_id=aad_object_id,
                text=text,
                consumer_name="MS Teams",
            )
            logger.info("[agents] on_message assistant_payload: %s", assistant_payload)
        except Exception as e:
            logger.exception("[agents] on_message: continue_conversation failed")
            await ctx.send_activity(_format_exception_message(e))
            return

        if assistant_payload and (
            assistant_payload.get("content")
            or assistant_payload.get("message_id")
            or assistant_payload.get("requires_confirmation")
        ):
            await _send_response_card(ctx, assistant_payload)
        else:
            logger.warning(
                "[agents] on_message: empty assistant payload for aad=%s", aad_object_id
            )
            debug_msg = assistant_payload.get("content") if assistant_payload else None
            await ctx.send_activity(debug_msg or "Hmm, I didn't get a reply")

    return on_message


async def on_invoke_feedback(ctx: TurnContext, _state: TurnState) -> None:
    value: dict[str, Any] = getattr(ctx.activity, "value", {}) or {}
    action: dict[str, Any] = (value.get("action") or value) or {}
    verb = str(action.get("verb") or "").lower()

    if verb in {"confirm_action_request", "reject_action_request"}:
        data: dict[str, Any] = action.get("data") or {}
        conversation_id = str(data.get("conversation_id") or "")
        trace_id = str(data.get("trace_id") or "")
        agent_system_name = str(data.get("agent_system_name") or "")
        request_ids_raw = data.get("request_ids") or []
        if isinstance(request_ids_raw, str):
            request_ids = [request_ids_raw]
        else:
            request_ids = [str(item) for item in request_ids_raw if item]

        logger.info(f"[agents] confirmation invoke data: {data}")
        confirmed_value = data.get("confirmed")
        if isinstance(confirmed_value, bool):
            confirmed = confirmed_value
        elif isinstance(confirmed_value, str):
            confirmed = confirmed_value.lower() == "true"
        else:
            confirmed = bool(confirmed_value)
        confirmation_card_payload = data.get("confirmation_card")

        aad_object_id = getattr(
            getattr(getattr(ctx, "activity", None), "from_property", None),
            "aad_object_id",
            None,
        )

        if not conversation_id or not agent_system_name or not aad_object_id:
            logger.error(
                "[agents] confirmation invoke missing data: conversation_id=%s agent_system_name=%s aad=%s",
                conversation_id,
                agent_system_name,
                aad_object_id,
            )
            await ctx.send_activity(
                "Sorry, I couldn't process the confirmation request."
            )
            return

        try:
            assistant_payload: (
                AssistantPayload | None
            ) = await handle_action_confirmation(
                agent_system_name=agent_system_name,
                user_id=aad_object_id,
                conversation_id=conversation_id,
                request_ids=request_ids,
                confirmed=confirmed,
                **observability_overrides(trace_id=trace_id, consumer_name="MS Teams"),
            )
        except Exception:
            await ctx.send_activity(
                "Sorry, something went wrong while processing the confirmation."
            )
            return

        ack_card = create_confirmation_result_card(confirmation_card_payload, confirmed)
        await ctx.send_activity(
            Activity(
                type="invokeResponse",
                value={
                    "status": 200,
                    "body": {
                        "statusCode": 200,
                        "type": "application/vnd.microsoft.card.adaptive",
                        "value": ack_card,
                    },
                },
            )
        )

        if assistant_payload:
            logger.info(
                "[agents] confirmation invoke assistant_payload: %s", assistant_payload
            )
            await _send_response_card(ctx, assistant_payload)
        else:
            logger.warning(
                "[agents] confirmation invoke returned empty payload (conversation=%s)",
                conversation_id,
            )
            await ctx.send_activity(
                "Thanks! I'll let you know if I find anything else."
            )
        return

    if verb not in {"like", "dislike", "close_conversation"}:
        logger.warning("[agents] unexpected feedback verb: %s", verb)
        return

    data: dict[str, Any] = action.get("data") or {}
    conversation_id = str(data.get("conversation_id") or "")
    message_id = str(data.get("message_id") or "")
    text = data.get("text") or None

    if not conversation_id or not message_id:
        logger.error(
            "[agents] missing IDs: conversation_id=%s, message_id=%s",
            conversation_id,
            message_id,
        )
        await ctx.send_activity("Sorry, feedback cannot be recorded (missing IDs).")
        return

    try:
        if verb == "like":
            feedback = LlmResponseFeedback(type=LlmResponseFeedbackType.LIKE)
            await set_message_feedback(
                conversation_id=conversation_id,
                message_id=message_id,
                data=feedback,
                consumer_name="MS Teams",
            )
            await _send_feedback_result_card(
                ctx,
                {
                    "conversation_id": conversation_id,
                    "text": text,
                    "reaction": "like",
                },
            )
        elif verb == "dislike":
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
            await set_message_feedback(
                conversation_id=conversation_id,
                message_id=message_id,
                data=feedback,
                consumer_name="MS Teams",
            )
            await _send_feedback_result_card(
                ctx,
                {
                    "conversation_id": conversation_id,
                    "text": text,
                    "reaction": "dislike",
                    "reason": reason.value,
                    "comment": comment,
                },
            )
        else:  # close_conversation
            await close_conversation_by_id(conversation_id)
            card_payload = {
                "conversation_id": conversation_id,
                "message_id": message_id,
                "content": text or "",
                "is_conversation_closed": True,
            }
            card = create_magnet_response_card(card_payload)
            await ctx.send_activity(
                Activity(
                    type="invokeResponse",
                    value={
                        "status": 200,
                        "body": {
                            "statusCode": 200,
                            "type": "application/vnd.microsoft.card.adaptive",
                            "value": card,
                        },
                    },
                )
            )
    except Exception:
        logger.exception(
            "[agents] invoke feedback error (conv=%s, msg=%s)",
            conversation_id,
            message_id,
        )
        await ctx.send_activity("Sorry, failed to record your feedback.")


def register_handlers(
    app: AgentApplication[TurnState], *, agent_system_name: str | None = None
) -> None:
    """Register the activity handlers on the provided application."""

    app.conversation_update("membersAdded")(
        _make_on_members_added_handler(agent_system_name or "")
    )
    app.activity("message")(_make_on_message_handler(agent_system_name or "", app))
    app.activity("invoke")(on_invoke_feedback)
