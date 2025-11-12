import json
import logging
import re
from copy import deepcopy
from typing import Any, Iterable

from slack_bolt.async_app import AsyncApp
from slack_bolt.context.respond.async_respond import AsyncRespond
from slack_bolt.context.say.async_say import AsyncSay
from slack_sdk.errors import SlackApiError
from slack_sdk.web.async_client import AsyncWebClient

from services.agents.conversations import set_message_feedback
from services.agents.utils.conversation_helpers import (
    AssistantPayload,
    close_conversation,
    close_conversation_by_id,
    continue_conversation,
    handle_action_confirmation,
    get_conversation_info,
    DEFAULT_AGENT_DISPLAY_NAME,
)
from services.agents.slack.blocks import build_welcome_message_blocks
from services.common.models import LlmResponseFeedback, LlmResponseFeedbackReason, LlmResponseFeedbackType
from .blocks import (
    create_assistant_response_blocks,
    create_confirmation_ack_blocks,
    to_slack_mrkdwn,
    update_blocks_with_feedback,
    update_blocks_with_closed_conversation,
)
from services.observability.utils import observability_overrides


logger = logging.getLogger(__name__)

_MENTION_PATTERN = re.compile(r"<@[^>]+>")
_PLACEHOLDER_TEXT = ":hourglass_flowing_sand: Magnet is thinking..."


def _strip_agent_mentions(text: str | None) -> str:
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


def attach_default_handlers(app: AsyncApp, agent_system_name: str, agent_display_name: str) -> None:
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

    async def _update_confirmation_message(
        client: AsyncWebClient,
        channel_id: str | None,
        message_ts: str | None,
        *,
        text: str,
        blocks: list[dict[str, Any]] | None,
        logger: logging.Logger,
        log_context: str,
    ) -> None:
        if not channel_id or not message_ts:
            logger.warning(
                "Cannot update confirmation message (%s) without channel or timestamp.",
                log_context,
            )
            return

        payload: dict[str, Any] = {
            "channel": channel_id,
            "ts": message_ts,
            "text": text,
        }
        if blocks:
            payload["blocks"] = blocks

        try:
            await client.chat_update(**payload)
        except SlackApiError:
            logger.exception(
                "Failed to update Slack message after %s (channel=%s ts=%s)",
                log_context,
                channel_id,
                message_ts,
            )

    async def _resolve_agent_display_name(
        context: dict[str, Any] | None,
        client: AsyncWebClient,
        logger: logging.Logger,
    ) -> str | None:
        agent_user_id = None
        if context:
            agent_user_id = context.get("bot_user_id") or context.get("botUserId")

        if not agent_user_id:
            return DEFAULT_AGENT_DISPLAY_NAME

        try:
            user_info = await client.users_info(user=agent_user_id)
        except SlackApiError:
            logger.warning("users.info failed while resolving agent display name (user=%s).", agent_user_id, exc_info=True)
            return None

        user_data = user_info.get("user") or {}
        profile = user_data.get("profile") or {}
        for candidate in (
            profile.get("display_name"),
            profile.get("real_name"),
            user_data.get("name"),
        ):
            if isinstance(candidate, str):
                candidate = candidate.strip()
                if candidate:
                    return candidate
        return None

    async def _respond_ephemeral(respond: AsyncRespond, text: str) -> None:
        await respond(text=text, response_type="ephemeral")

    async def _handle_conversation_closure_command(
        command_name: str,
        ack: Any,
        body: dict[str, Any],
        respond: AsyncRespond,
        logger: logging.Logger,
    ) -> None:
        await ack()

        user_id = body.get("user_id")
        if not user_id:
            logger.warning("Missing user_id in %s command payload: %s", command_name, body)
            await _respond_ephemeral(respond, "I couldn't determine which conversation to close.")
            return

        try:
            result = await close_conversation(agent_system_name=agent_system_name, user_id=user_id)
        except Exception:
            logger.exception("Failed to close conversation via %s command.", command_name)
            result = "Failed to close the conversation."

        await _respond_ephemeral(respond, result)

    async def _handle_conversation_info_command(
        ack: Any,
        body: dict[str, Any],
        respond: AsyncRespond,
        logger: logging.Logger,
    ) -> None:
        await ack()

        user_id = body.get("user_id")
        if not user_id:
            logger.warning("Missing user_id in /get_conversation_info payload: %s", body)
            await _respond_ephemeral(respond, "I couldn't determine which conversation to inspect.")
            return

        try:
            result = await get_conversation_info(agent_system_name=agent_system_name, user_id=user_id)
        except Exception:
            logger.exception("Failed to gather conversation info via /get_conversation_info.")
            result = "Failed to load the last conversation."

        await _respond_ephemeral(respond, result)

    async def _handle_action_confirmation_interaction(
        ack: Any,
        body: dict[str, Any],
        client: AsyncWebClient,
        logger: logging.Logger,
    ) -> None:
        await ack()

        action = _get_first(body.get("actions") or [])
        if not isinstance(action, dict):
            logger.warning("Confirmation action payload is missing action details: %s", body)
            return

        raw_value = action.get("value") or ""
        try:
            confirmation_payload = json.loads(raw_value) if raw_value else {}
        except (TypeError, ValueError):
            logger.warning("Failed to parse confirmation payload: %s", raw_value)
            return

        confirmed = bool(confirmation_payload.get("confirmed"))
        conversation_id = confirmation_payload.get("conversation_id")
        trace_id = confirmation_payload.get("trace_id")
        agent_name = (
            confirmation_payload.get("agent_system_name")
            or agent_system_name
        )
        confirmation_card_payload = (
            confirmation_payload.get("confirmation_card") or {}
        )

        raw_request_ids = confirmation_payload.get("request_ids") or []
        if isinstance(raw_request_ids, list):
            request_ids = [str(item) for item in raw_request_ids if item]
        elif raw_request_ids:
            request_ids = [str(raw_request_ids)]
        else:
            request_ids = []

        user_id = (body.get("user") or {}).get("id")
        channel_id = (body.get("channel") or {}).get("id") or body.get("container", {}).get("channel_id")
        message_ts = (body.get("message") or {}).get("ts") or body.get("container", {}).get("message_ts")

        if not conversation_id or not user_id or not request_ids:
            logger.warning(
                "Confirmation interaction missing data (conversation=%s user=%s request_ids=%s)",
                conversation_id,
                user_id,
                request_ids,
            )
            warning_text = ":warning: Sorry, I couldn't process your confirmation."
            await _update_confirmation_message(
                client,
                channel_id,
                message_ts,
                text=warning_text,
                blocks=[
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": warning_text},
                    }
                ],
                logger=logger,
                log_context="action_confirmation_missing_data",
            )
            return

        try:
            assistant_payload = await handle_action_confirmation(
                agent_system_name=agent_name,
                user_id=user_id,
                conversation_id=conversation_id,
                request_ids=request_ids,
                confirmed=confirmed,
                **observability_overrides(trace_id=trace_id, consumer_name="Slack"),
            )
        except Exception:
            logger.exception(
                "Failed to process action confirmation (conversation=%s user=%s)",
                conversation_id,
                user_id,
            )
            error_text = ":warning: Something went wrong while processing your response."
            await _update_confirmation_message(
                client,
                channel_id,
                message_ts,
                text=error_text,
                blocks=[
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": error_text},
                    }
                ],
                logger=logger,
                log_context="action_confirmation_failure",
            )
            return

        ack_text = ":white_check_mark: Action confirmed." if confirmed else ":x: Action rejected."
        ack_blocks = create_confirmation_ack_blocks(confirmation_card_payload, confirmed)

        await _update_confirmation_message(
            client,
            channel_id,
            message_ts,
            text=ack_text,
            blocks=ack_blocks,
            logger=logger,
            log_context="action_confirmation_update",
        )

        if not assistant_payload:
            logger.info(
                "Confirmation interaction returned no follow-up payload (conversation=%s)",
                conversation_id,
            )
            return

        if not channel_id:
            logger.warning(
                "Missing channel_id for follow-up response after confirmation (conversation=%s)",
                conversation_id,
            )
            return

        fallback_text = to_slack_mrkdwn(_payload_text(assistant_payload)) or "Magnet response"
        response_blocks = create_assistant_response_blocks(assistant_payload)
        follow_up_payload: dict[str, Any] = {
            "channel": channel_id,
            "text": fallback_text,
        }
        if response_blocks:
            follow_up_payload["blocks"] = response_blocks

        try:
            await client.chat_postMessage(**follow_up_payload)
        except SlackApiError:
            logger.exception(
                "Failed to send follow-up response after confirmation (conversation=%s channel=%s)",
                conversation_id,
                channel_id,
            )

    @app.command("/welcome")
    async def handle_welcome_command(
        ack: Any,
        body: dict[str, Any],
        client: AsyncWebClient,
        respond: AsyncRespond,
        logger: logging.Logger,
        context: dict[str, Any] | None = None,
    ) -> None:
        await ack()

        agent_display_name = await _resolve_agent_display_name(context, client, logger)
        blocks,message_text = build_welcome_message_blocks(agent_display_name, agent_display_name)

        try:
            await respond(
                text=message_text,
                blocks=blocks,
                response_type="ephemeral",
            )
        except Exception:
            logger.exception("Failed to deliver welcome card response.")

    @app.command("/restart")
    async def handle_restart_command(
        ack: Any,
        body: dict[str, Any],
        respond: AsyncRespond,
        logger: logging.Logger,
    ) -> None:
        await _handle_conversation_closure_command("/restart", ack, body, respond, logger)

    @app.command("/get_conversation_info")
    async def handle_get_conversation_info_command(
        ack: Any,
        body: dict[str, Any],
        respond: AsyncRespond,
        logger: logging.Logger,
    ) -> None:
        await _handle_conversation_info_command(ack, body, respond, logger)

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
        user_message = _strip_agent_mentions(event.get("text"))
        if not user_message:
            logger.info("Ignoring empty app mention message on channel %s", channel)
            return

        logger.info("app mention received channel=%s", channel)

        placeholder_ts = await _send_placeholder_message(client, channel, logger)

        try:
            assistant_payload = await continue_conversation(
                agent_system_name=agent_system_name,
                user_id=user_id,
                text=user_message,
                consumer_name="Slack",
            )
        except Exception:
            logger.exception("Error while continuing conversation for app_mention (channel=%s)", channel)
            await _handle_error_message(client, channel, placeholder_ts, logger, "app_mention")
            return

        raw_text = _payload_text(assistant_payload)
        fallback_text = to_slack_mrkdwn(raw_text)
        if not fallback_text:
            if assistant_payload and (
                assistant_payload.get("requires_confirmation")
            ):
                fallback_text = "Magnet needs your confirmation before running the requested action."
            else:
                fallback_text = "Magnet response"
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
                user_id=user_id,
                text=user_message,
                consumer_name="Slack",
            )
        except Exception:
            logger.exception("Error while continuing conversation for message (channel=%s)", channel)
            await _handle_error_message(client, channel, placeholder_ts, logger, "message")
            return

        raw_text = _payload_text(assistant_payload)
        fallback_text = to_slack_mrkdwn(raw_text)
        if not fallback_text:
            if assistant_payload and (
                assistant_payload.get("requires_confirmation")
            ):
                fallback_text = "Magnet needs your confirmation before running the requested action."
            else:
                fallback_text = "Magnet answer"
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


    @app.action("confirm_action_request")
    async def handle_confirm_action_request(
        ack: Any,
        body: dict[str, Any],
        client: AsyncWebClient,
        logger: logging.Logger,
    ) -> None:
        await _handle_action_confirmation_interaction(ack, body, client, logger)


    @app.action("reject_action_request")
    async def handle_reject_action_request(
        ack: Any,
        body: dict[str, Any],
        client: AsyncWebClient,
        logger: logging.Logger,
    ) -> None:
        await _handle_action_confirmation_interaction(ack, body, client, logger)


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

        message_id = payload.get("message_id")
        conversation_id = payload.get("conversation_id")
        logger.info(
            "like_answer payload: channel=%s ts=%s message_id=%s conversation_id=%s",
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
                consumer_name="Slack",
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

        message_id = payload.get("message_id")
        conversation_id = payload.get("conversation_id")
        logger.info(
            "dislike_answer payload: channel=%s ts=%s message_id=%s conversation_id=%s",
            channel_id,
            ts,
            message_id,
            conversation_id,
        )

        metadata_payload: dict[str, Any] = {
            "channel_id": channel_id,
            "ts": ts,
            "message_id": message_id,
            "conversation_id": conversation_id,
        }

        view = {
            "type": "modal",
            "callback_id": "dislike_feedback_modal",
            "private_metadata": json.dumps(metadata_payload),
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


    @app.action("close_conversation")
    async def handle_close_conversation(
        body: dict[str, Any],
        ack: Any,
        respond: AsyncRespond,
        logger: logging.Logger,
    ) -> None:
        await ack()

        message_blocks = body.get("message", {}).get("blocks") or []
        action = _get_first(body.get("actions") or [])
        payload: dict[str, Any] = {}
        if action and action.get("value"):
            try:
                payload = json.loads(action["value"])
            except (TypeError, ValueError):
                logger.warning("Failed to parse close_conversation action payload: %s", action["value"])

        conversation_id = payload.get("conversation_id")
        message_id = payload.get("message_id")
        logger.info(
            "close_conversation payload: conversation_id=%s message_id=%s",
            conversation_id,
            message_id,
        )

        if not conversation_id:
            try:
                await respond(
                    {
                        "response_type": "ephemeral",
                        "text": "I couldn't determine which conversation to close.",
                    }
                )
            except Exception:
                logger.exception("Failed to send close_conversation missing ID response.")
            return

        try:
            await close_conversation_by_id(conversation_id)
        except Exception:
            logger.exception(
                "Failed to close conversation via button (conversation_id=%s message_id=%s)",
                conversation_id,
                message_id,
            )
            try:
                await respond(
                    {
                        "response_type": "ephemeral",
                        "text": "Failed to close the conversation. Please try again.",
                    }
                )
            except Exception:
                logger.exception("Failed to send close_conversation failure response.")
            return

        updated_blocks = update_blocks_with_closed_conversation(message_blocks)
        try:
            await respond(
                {
                    "replace_original": True,
                    "text": "Conversation closed.",
                    "blocks": updated_blocks or message_blocks,
                }
            )
        except Exception:
            logger.exception(
                "Failed to update message after close_conversation action (conversation_id=%s message_id=%s)",
                conversation_id,
                message_id,
            )


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

        channel_id = metadata.get("channel_id")
        ts = metadata.get("ts")
        message_id = metadata.get("message_id")
        conversation_id = metadata.get("conversation_id")
        initial_blocks: list[dict[str, Any]] = []
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

        history_blocks: list[dict[str, Any]] = deepcopy(initial_blocks)
        if channel_id and ts:
            try:
                history = await client.conversations_history(
                    channel=channel_id,
                    latest=ts,
                    inclusive=True,
                    limit=1,
                )
                history_blocks = (history.get("messages") or [{}])[0].get("blocks") or []
                logger.debug(
                    "dislike_feedback_modal fetched blocks: channel=%s ts=%s blocks_count=%s",
                    channel_id,
                    ts,
                    len(history_blocks),
                )
            except SlackApiError:
                logger.exception("Failed to fetch conversation history for dislike feedback.")

        updated_blocks = update_blocks_with_feedback(
            history_blocks,
            "dislike_answer",
            {"reason": reason, "comment": comment},
        )
        logger.debug(
            "dislike_feedback_modal updated blocks prepared: channel=%s ts=%s updated_count=%s",
            channel_id,
            ts,
            len(updated_blocks),
        )

        if channel_id and ts:
            try:
                response = await client.chat_update(
                    channel=channel_id,
                    ts=ts,
                    text="Thanks for your feedback!",
                    blocks=updated_blocks or history_blocks,
                )
                if not response.get("ok", False):
                    logger.warning(
                        "chat_update returned non-ok for dislike feedback (channel=%s ts=%s error=%s)",
                        channel_id,
                        ts,
                        response.get("error"),
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
                    consumer_name="Slack",
                )
            except Exception:
                logger.exception(
                    "Failed to persist dislike feedback (conversation=%s message=%s)",
                    conversation_id,
                    message_id,
                )
