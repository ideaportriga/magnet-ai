import json
import logging
import re
from typing import Any, Iterable

from slack_bolt.async_app import AsyncApp
from slack_bolt.context.respond.async_respond import AsyncRespond
from slack_bolt.context.say.async_say import AsyncSay
from slack_sdk.errors import SlackApiError
from slack_sdk.web.async_client import AsyncWebClient

from services.agents.conversations import set_message_feedback
from services.agents.utils.conversation_helpers import AssistantPayload, continue_conversation
from services.common.models import LlmResponseFeedback, LlmResponseFeedbackReason, LlmResponseFeedbackType
from .blocks import create_assistant_response_blocks, to_slack_mrkdwn, update_blocks_with_feedback

logger = logging.getLogger(__name__)

_MENTION_PATTERN = re.compile(r"<@[^>]+>")
_PLACEHOLDER_TEXT = ":hourglass_flowing_sand: Magnet is thinking..."


def _strip_bot_mentions(text: str | None) -> str:
    if not text:
        return ""

    without_mentions = _MENTION_PATTERN.sub("", text)
    return without_mentions.strip()


def _payload_text(payload: AssistantPayload | None) -> str | None:
    if not payload:
        return None

    content = payload.get("content")
    if content is None:
        return None

    if isinstance(content, str):
        return content

    try:
        return json.dumps(content, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(content)


def _get_first(iterable: Iterable[Any]) -> Any:
    for item in iterable:
        return item
    return None


def attach_default_handlers(app: AsyncApp, agent_system_name: str) -> None:
    async def _send_placeholder_message(
        client: AsyncWebClient,
        channel: str,
        logger: logging.Logger,
    ) -> str | None:
        try:
            response = await client.chat_postMessage(channel=channel, text=_PLACEHOLDER_TEXT)
        except SlackApiError:
            logger.warning("Failed to send placeholder message (channel=%s)", channel, exc_info=True)
            return None

        return response.get("ts")

    async def _finalize_response_message(
        client: AsyncWebClient,
        channel: str,
        message_payload: dict[str, Any],
        placeholder_ts: str | None,
        logger: logging.Logger,
        *,
        log_context: str,
    ) -> None:
        payload = {"channel": channel, **message_payload}
        if placeholder_ts:
            try:
                await client.chat_update(ts=placeholder_ts, **payload)
                return
            except SlackApiError:
                logger.warning(
                    "Failed to update placeholder message (%s channel=%s ts=%s)",
                    log_context,
                    channel,
                    placeholder_ts,
                    exc_info=True,
                )

        try:
            await client.chat_postMessage(**payload)
        except SlackApiError:
            logger.exception(
                "Failed to deliver Slack response (%s channel=%s)",
                log_context,
                channel,
            )

    async def _handle_error_message(
        client: AsyncWebClient,
        channel: str,
        placeholder_ts: str | None,
        logger: logging.Logger,
        log_context: str,
    ) -> None:
        error_payload: dict[str, Any] = {
            "text": ":warning: Sorry, something went wrong while preparing my response.",
        }
        await _finalize_response_message(
            client,
            channel,
            error_payload,
            placeholder_ts,
            logger,
            log_context=log_context,
        )

    @app.event("app_mention")
    async def handle_app_mention(
        event: dict[str, Any],
        context: dict[str, Any],
        client: AsyncWebClient,
        logger: logging.Logger,
    ) -> None:
        channel = event.get("channel")
        if not channel:
            logger.warning("Slack app_mention event is missing channel information: %s", event)
            return

        user_id = event.get("user") or context.get("user_id") or channel
        user_message = _strip_bot_mentions(event.get("text"))
        if not user_message:
            logger.info("Ignoring empty app mention message on channel %s", channel)
            return

        logger.info("app mention received channel=%s", channel)

        placeholder_ts = await _send_placeholder_message(client, channel, logger)

        try:
            assistant_payload = await continue_conversation(
                agent_system_name=agent_system_name,
                aad_object_id=user_id,
                text=user_message,
            )
        except Exception:
            logger.exception("Error while continuing conversation for app_mention (channel=%s)", channel)
            await _handle_error_message(client, channel, placeholder_ts, logger, "app_mention")
            return

        raw_text = _payload_text(assistant_payload)
        fallback_text = to_slack_mrkdwn(raw_text)
        blocks = create_assistant_response_blocks(assistant_payload)
        message_payload: dict[str, Any] = {"text": fallback_text}
        if blocks:
            message_payload["blocks"] = blocks

        await _finalize_response_message(
            client,
            channel,
            message_payload,
            placeholder_ts,
            logger,
            log_context="app_mention",
        )


    @app.event("message")
    async def handle_message_event(
        event: dict[str, Any],
        context: dict[str, Any],
        say: AsyncSay,
        client: AsyncWebClient,
        logger: logging.Logger,
    ) -> None:
        channel = event.get("channel")
        subtype = event.get("subtype")
        user_id = event.get("user")
        if subtype or not user_id or not channel:
            return

        user_message = (event.get("text") or "").strip()
        if not user_message:
            return

        logger.info("message received channel=%s", channel)

        placeholder_ts = await _send_placeholder_message(client, channel, logger)

        try:
            assistant_payload = await continue_conversation(
                agent_system_name=agent_system_name,
                aad_object_id=user_id,
                text=user_message,
            )
        except Exception:
            logger.exception("Error while continuing conversation for message (channel=%s)", channel)
            await _handle_error_message(client, channel, placeholder_ts, logger, "message")
            return

        raw_text = _payload_text(assistant_payload)
        fallback_text = to_slack_mrkdwn(raw_text) or "Magnet answer"
        blocks = create_assistant_response_blocks(assistant_payload)
        message_payload: dict[str, Any] = {"text": fallback_text}
        if blocks:
            message_payload["blocks"] = blocks

        await _finalize_response_message(
            client,
            channel,
            message_payload,
            placeholder_ts,
            logger,
            log_context="message",
        )


    @app.error
    async def handle_error(error: Exception, body: dict, say: AsyncSay, logger: logging.Logger) -> None:
        error_message = f"Bolt app error: {error}"
        logger.error(error_message, exc_info=error)
        # Also send the error message to the chat if possible
        channel = None
        # Try to get the channel from the incoming event/body
        if isinstance(body, dict):
            channel = (
                body.get("event", {}).get("channel")
                or body.get("channel", {}).get("id")
                or body.get("container", {}).get("channel_id")
            )
        if channel:
            try:
                await say(channel=channel, text=f":warning: {error_message}")
            except Exception:
                logger.error("Failed to send error message to channel %s", channel)


    @app.action("like_answer")
    async def handle_like_answer(
        body: dict[str, Any],
        ack: Any,
        respond: AsyncRespond,
        logger: logging.Logger,
    ) -> None:
        await ack()

        channel_id = (
            body.get("channel", {}).get("id")
            or body.get("container", {}).get("channel_id")
        )
        ts = body.get("message", {}).get("ts") or body.get("container", {}).get("message_ts")
        message_blocks = body.get("message", {}).get("blocks") or []
        action = _get_first(body.get("actions") or [])
        payload: dict[str, Any] = {}
        if action and action.get("value"):
            try:
                payload = json.loads(action["value"])
            except (TypeError, ValueError):
                logger.warning("Failed to parse like_answer action payload: %s", action["value"])

        message_id = payload.get("messageId")
        conversation_id = payload.get("conversationId")
        logger.info(
            "like_answer payload: channel=%s ts=%s messageId=%s conversationId=%s",
            channel_id,
            ts,
            message_id,
            conversation_id,
        )

        if not channel_id or not ts or not message_blocks:
            logger.warning("Incomplete like_answer payload, skipping update.")
            return

        updated_blocks = update_blocks_with_feedback(message_blocks, "like_answer")
        try:
            await respond(
                {
                    "replace_original": True,
                    "text": "Thanks for your feedback!",
                    "blocks": updated_blocks or message_blocks,
                }
            )
        except Exception:
            logger.exception("Failed to respond to like_answer action.")

        if not conversation_id or not message_id:
            return

        feedback = LlmResponseFeedback(type=LlmResponseFeedbackType.LIKE)
        try:
            await set_message_feedback(
                conversation_id=conversation_id,
                message_id=message_id,
                data=feedback,
            )
        except Exception:
            logger.exception("Failed to persist like feedback (conversation=%s message=%s)", conversation_id, message_id)


    @app.action("dislike_answer")
    async def handle_dislike_answer(
        body: dict[str, Any],
        ack: Any,
        client: AsyncWebClient,
        logger: logging.Logger,
    ) -> None:
        await ack()

        channel_id = (
            body.get("channel", {}).get("id")
            or body.get("container", {}).get("channel_id")
        )
        ts = body.get("message", {}).get("ts") or body.get("container", {}).get("message_ts")
        action = _get_first(body.get("actions") or [])
        payload: dict[str, Any] = {}
        if action and action.get("value"):
            try:
                payload = json.loads(action["value"])
            except (TypeError, ValueError):
                logger.warning("Failed to parse dislike_answer action payload: %s", action["value"])

        message_id = payload.get("messageId")
        conversation_id = payload.get("conversationId")
        logger.info(
            "dislike_answer payload: channel=%s ts=%s messageId=%s conversationId=%s",
            channel_id,
            ts,
            message_id,
            conversation_id,
        )

        view = {
            "type": "modal",
            "callback_id": "dislike_feedback_modal",
            "private_metadata": json.dumps(
                {
                    "channelId": channel_id,
                    "ts": ts,
                    "messageId": message_id,
                    "conversationId": conversation_id,
                }
            ),
            "title": {"type": "plain_text", "text": "Feedback"},
            "submit": {"type": "plain_text", "text": "Submit"},
            "close": {"type": "plain_text", "text": "Cancel"},
            "blocks": [
                {
                    "type": "input",
                    "block_id": "reason_select_block",
                    "element": {
                        "type": "static_select",
                        "action_id": "reason_select",
                        "placeholder": {"type": "plain_text", "text": "Select a reason"},
                        "initial_option": {
                            "text": {"type": "plain_text", "text": "Other"},
                            "value": "other",
                        },
                        "options": [
                            {"text": {"type": "plain_text", "text": "Not relevant"}, "value": "not_relevant"},
                            {"text": {"type": "plain_text", "text": "Inaccurate"}, "value": "inaccurate"},
                            {"text": {"type": "plain_text", "text": "Outdated"}, "value": "outdated"},
                            {"text": {"type": "plain_text", "text": "Other"}, "value": "other"},
                        ],
                    },
                    "label": {"type": "plain_text", "text": "Reason"},
                },
                {
                    "type": "input",
                    "block_id": "comment_block",
                    "optional": True,
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "comment_input",
                        "multiline": True,
                        "placeholder": {"type": "plain_text", "text": "Optional comment"},
                    },
                    "label": {"type": "plain_text", "text": "Comment"},
                },
            ],
        }

        try:
            await client.views_open(trigger_id=body.get("trigger_id"), view=view)
        except SlackApiError:
            logger.exception("views.open failed for dislike_answer action.")


    @app.action("open_conversation")
    async def handle_open_conversation(ack: Any) -> None:
        await ack()


    @app.action("open_magnet_ai")
    async def handle_open_magnet_ai(ack: Any) -> None:
        await ack()


    @app.view("dislike_feedback_modal")
    async def handle_dislike_feedback_modal(
        ack: Any,
        body: dict[str, Any],
        view: dict[str, Any],
        client: AsyncWebClient,
        logger: logging.Logger,
    ) -> None:
        await ack()

        metadata_raw = view.get("private_metadata")
        metadata: dict[str, Any] = {}
        if metadata_raw:
            try:
                metadata = json.loads(metadata_raw)
            except (TypeError, ValueError):
                logger.warning("Failed to parse private metadata for dislike modal: %s", metadata_raw)

        channel_id = metadata.get("channelId")
        ts = metadata.get("ts")
        message_id = metadata.get("messageId")
        conversation_id = metadata.get("conversationId")
        reason = (
            view.get("state", {})
            .get("values", {})
            .get("reason_select_block", {})
            .get("reason_select", {})
            .get("selected_option", {})
            .get("value", "other")
        )
        comment = (
            view.get("state", {})
            .get("values", {})
            .get("comment_block", {})
            .get("comment_input", {})
            .get("value", "")
        )

        history_blocks: list[dict[str, Any]] = []
        if channel_id and ts:
            try:
                history = await client.conversations_history(
                    channel=channel_id,
                    latest=ts,
                    inclusive=True,
                    limit=1,
                )
                history_blocks = (history.get("messages") or [{}])[0].get("blocks") or []
            except SlackApiError:
                logger.exception("Failed to fetch conversation history for dislike feedback.")

        updated_blocks = update_blocks_with_feedback(
            history_blocks,
            "dislike_answer",
            {"reason": reason, "comment": comment},
        )

        if channel_id and ts:
            try:
                await client.chat_update(
                    channel=channel_id,
                    ts=ts,
                    text="Thanks for your feedback!",
                    blocks=updated_blocks or history_blocks,
                )
            except SlackApiError:
                logger.exception("Failed to update message after dislike feedback (channel=%s ts=%s)", channel_id, ts)

        if conversation_id and message_id:
            reason_value = reason or "other"
            try:
                reason_enum = LlmResponseFeedbackReason(reason_value)
            except ValueError:
                reason_enum = LlmResponseFeedbackReason.OTHER
            feedback = LlmResponseFeedback(
                type=LlmResponseFeedbackType.DISLIKE,
                reason=reason_enum,
                comment=comment or None,
            )
            try:
                await set_message_feedback(
                    conversation_id=conversation_id,
                    message_id=message_id,
                    data=feedback,
                )
            except Exception:
                logger.exception(
                    "Failed to persist dislike feedback (conversation=%s message=%s)",
                    conversation_id,
                    message_id,
                )
