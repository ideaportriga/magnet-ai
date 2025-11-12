import json
from typing import Any

from services.agents.utils.conversation_helpers import (
    WELCOME_LEARN_MORE_URL,
    AssistantPayload,
)
from services.agents.utils.markdown import to_slack_mrkdwn


def _normalize_content(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    try:
        return json.dumps(content, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(content)


def _truncate(text: str, max_length: int = 100) -> str:
    if max_length <= 0:
        return ""
    if len(text) <= max_length:
        return text
    return text[: max_length - 1] + "..."


def create_confirmation_blocks(
    payload: AssistantPayload | None,
) -> list[dict[str, Any]]:
    if not payload:
        return []

    conversation_id = payload.get("conversation_id")
    message_id = payload.get("message_id")
    trace_id = payload.get("trace_id")
    agent_system_name = payload.get("agent_system_name")

    raw_requests = payload.get("action_requests") or []
    request_ids = [
        str(request.get("id"))
        for request in raw_requests
        if isinstance(request, dict) and request.get("id")
    ]

    header_text = "AI Assistant Requires Confirmation"

    confirmation_messages: list[str] = []
    if raw_requests:
        multiple = len(raw_requests) > 1
        for index, request in enumerate(raw_requests, start=1):
            if not isinstance(request, dict):
                continue
            message = (
                request.get("action_message") or "The assistant requested an action."
            )
            prefix = f"{index}. " if multiple else ""
            confirmation_messages.append(f"{prefix}{message}")
    if not confirmation_messages:
        confirmation_messages = ["The assistant requested an action."]

    confirmation_payload = {
        "header": header_text,
        "messages": confirmation_messages,
    }

    common_payload = {
        "conversation_id": conversation_id,
        "trace_id": trace_id,
        "message_id": message_id,
        "agent_system_name": agent_system_name,
        "request_ids": request_ids,
        "confirmation_card": confirmation_payload,
    }

    blocks: list[dict[str, Any]] = [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*{to_slack_mrkdwn(header_text)}*"},
        }
    ]
    for message in confirmation_messages:
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": to_slack_mrkdwn(message),
                },
            }
        )

    blocks.append(
        {
            "type": "actions",
            "block_id": "action_confirmation_block",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Confirm", "emoji": True},
                    "style": "primary",
                    "action_id": "confirm_action_request",
                    "value": json.dumps({**common_payload, "confirmed": True}),
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Reject", "emoji": True},
                    "style": "danger",
                    "action_id": "reject_action_request",
                    "value": json.dumps({**common_payload, "confirmed": False}),
                },
            ],
        }
    )

    return blocks


def create_confirmation_ack_blocks(
    confirmation_payload: dict[str, Any] | None,
    confirmed: bool,
) -> list[dict[str, Any]]:
    payload = confirmation_payload or {}
    header_text = payload.get("header") or "AI Assistant Requires Confirmation"
    messages = payload.get("messages") or ["The assistant requested an action."]

    status_text = (
        ":white_check_mark: You confirmed this action."
        if confirmed
        else ":x: You rejected this action."
    )

    blocks: list[dict[str, Any]] = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{to_slack_mrkdwn(str(header_text))}*",
            },
        }
    ]

    for message in messages:
        text = to_slack_mrkdwn(str(message))
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"> {text}"},
            }
        )

    blocks.append(
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": status_text,
                }
            ],
        }
    )

    return blocks


def create_assistant_response_blocks(
    payload: AssistantPayload | None,
) -> list[dict[str, Any]]:
    if not payload:
        return []

    requires_confirmation = bool(payload.get("requires_confirmation"))

    action_requests = payload.get("action_requests") or []
    if requires_confirmation and action_requests:
        return create_confirmation_blocks(payload)

    message_id = payload.get("message_id")
    conversation_id = payload.get("conversation_id")
    content = payload.get("content") or "No answer available."

    raw_text = _normalize_content(content)
    mrkdwn_text = to_slack_mrkdwn(raw_text)
    text = _truncate(mrkdwn_text, 2900)

    blocks: list[dict[str, Any]] = [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": text},
        },
        {"type": "divider"},
    ]

    elements: list[dict[str, Any]] = [
        {
            "type": "button",
            "text": {"type": "plain_text", "text": "👍", "emoji": True},
            "action_id": "like_answer",
            "style": "primary",
            "value": json.dumps(
                {
                    "feedback": "like",
                    "message_id": message_id,
                    "conversation_id": conversation_id,
                }
            ),
        },
        {
            "type": "button",
            "text": {"type": "plain_text", "text": "👎", "emoji": True},
            "action_id": "dislike_answer",
            "style": "danger",
            "value": json.dumps(
                {
                    "feedback": "dislike",
                    "message_id": message_id,
                    "conversation_id": conversation_id,
                }
            ),
        },
    ]

    if conversation_id:
        elements.append(
            {
                "type": "button",
                "action_id": "close_conversation",
                "text": {"type": "plain_text", "text": "🔒", "emoji": True},
                "value": json.dumps(
                    {"message_id": message_id, "conversation_id": conversation_id}
                ),
            }
        )

    blocks.append(
        {
            "type": "actions",
            "block_id": "feedback_actions_block",
            "elements": elements,
        }
    )

    return blocks


def update_blocks_with_feedback(
    blocks: list[dict[str, Any]] | None,
    action: str,
    details: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Update existing Slack blocks with feedback state."""
    existing_blocks = list(blocks or [])
    feedback_action = action or ""
    data = details or {}

    if feedback_action == "like_answer":
        message = "Thanks for your feedback: *Like*"
    else:
        message = "Thanks for your feedback: *Do not like*"

    if feedback_action == "dislike_answer":
        message += f"\nReason: {data.get('reason')}"
        comment = data.get("comment")
        if comment:
            message += f"\nComment: {comment}"

    feedback_context = {
        "type": "context",
        "block_id": "feedback_block",
        "elements": [
            {
                "type": "mrkdwn",
                "text": message,
            }
        ],
    }

    target_index = -1
    for idx, block in enumerate(existing_blocks):
        if not isinstance(block, dict):
            continue
        if block.get("type") != "actions":
            continue
        elements = block.get("elements") or []
        if not isinstance(elements, list):
            continue
        for element in elements:
            if not isinstance(element, dict):
                continue
            action_id = element.get("action_id")
            if action_id in {"like_answer", "dislike_answer"}:
                target_index = idx
                break
        if target_index >= 0:
            break

    if target_index >= 0:
        block = existing_blocks[target_index] or {}
        elements = block.get("elements")
        if not isinstance(elements, list):
            elements = []
        filtered = []
        for element in elements:
            if not isinstance(element, dict):
                continue
            action_id = element.get("action_id")
            if action_id in {"like_answer", "dislike_answer"}:
                continue
            filtered.append(element)

        if filtered:
            updated_block = {
                "type": "actions",
                "elements": filtered,
            }
            block_id = block.get("block_id")
            if isinstance(block_id, str) and block_id:
                updated_block["block_id"] = block_id
            existing_blocks[target_index] = {
                **updated_block,
            }
            existing_blocks.insert(target_index + 1, feedback_context)
        else:
            existing_blocks[target_index] = feedback_context
    else:
        existing_blocks.append(feedback_context)

    return existing_blocks


def update_blocks_with_closed_conversation(
    blocks: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    """Remove the close button and add a status note when a conversation is closed."""
    existing_blocks = list(blocks or [])
    status_insert_index: int | None = None

    for idx, block in enumerate(existing_blocks):
        if not isinstance(block, dict):
            continue
        if block.get("type") != "actions":
            continue
        elements = block.get("elements")
        if not isinstance(elements, list):
            continue

        filtered: list[dict[str, Any]] = []
        removed = False
        for element in elements:
            if not isinstance(element, dict):
                continue
            if element.get("action_id") == "close_conversation":
                removed = True
                continue
            filtered.append(element)

        if not removed:
            continue

        if filtered:
            updated_block = dict(block)
            updated_block["elements"] = filtered
            existing_blocks[idx] = updated_block
            status_insert_index = idx + 1
        else:
            existing_blocks.pop(idx)
            status_insert_index = idx
        break

    if status_insert_index is None:
        return existing_blocks

    already_has_status = any(
        isinstance(block, dict) and block.get("block_id") == "conversation_status_block"
        for block in existing_blocks
    )
    if already_has_status:
        return existing_blocks

    status_block = {
        "type": "context",
        "block_id": "conversation_status_block",
        "elements": [
            {
                "type": "mrkdwn",
                "text": ":lock: Conversation closed.",
            }
        ],
    }

    if status_insert_index >= len(existing_blocks):
        existing_blocks.append(status_block)
    else:
        existing_blocks.insert(status_insert_index, status_block)

    return existing_blocks


def build_welcome_message_blocks(
    bot_name: str, agent_display_name: str | None
) -> list[dict[str, Any]]:
    message_intro = f":wave: Hi there! I'm *{bot_name}* and I'm happy to connect you with {agent_display_name}."
    message_tips = (
        "- Mention me in a channel to ask a question together with your team.\n"
        "- Send me a direct message to have the conversation privately.\n"
        "- Use the feedback buttons under my replies to help me improve."
    )

    blocks: list[dict[str, Any]] = [
        {"type": "section", "text": {"type": "mrkdwn", "text": message_intro}},
        {"type": "section", "text": {"type": "mrkdwn", "text": message_tips}},
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "action_id": "open_magnet_ai",
                    "text": {"type": "plain_text", "text": "Learn more", "emoji": True},
                    "url": WELCOME_LEARN_MORE_URL,
                }
            ],
        },
    ]

    return blocks, message_intro
