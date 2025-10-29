import json
import os
import re
from typing import Any

from services.agents.utils.conversation_helpers import AssistantPayload

_BOLD_PATTERN = re.compile(r"\*\*([^*\n]+)\*\*")


def _escape_link_text(text: str) -> str:
    return text.replace("|", r"\|")


def _escape_link_url(url: str) -> str:
    replacements = {
        " ": "%20",
        "<": "%3C",
        ">": "%3E",
        "|": "%7C",
    }
    for char, replacement in replacements.items():
        url = url.replace(char, replacement)
    return url


def _rewrite_links(markdown: str) -> str:
    """Convert [label](url) patterns into Slack's <url|label> format."""
    if "[" not in markdown:
        return markdown

    result: list[str] = []
    index = 0
    length = len(markdown)

    while index < length:
        start = markdown.find("[", index)
        if start == -1:
            result.append(markdown[index:])
            break

        close_label = markdown.find("](", start)
        if close_label == -1:
            result.append(markdown[index:])
            break

        label = markdown[start + 1 : close_label]
        url_start = close_label + 2
        pos = url_start
        depth = 1

        while pos < length and depth > 0:
            char = markdown[pos]
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    break
            pos += 1

        if depth != 0:
            result.append(markdown[index:])
            break

        url = markdown[url_start:pos]
        result.append(markdown[index:start])
        formatted = f"<{_escape_link_url(url.strip())}|{_escape_link_text(label.strip())}>"
        result.append(formatted)
        index = pos + 1

    return "".join(result)


def to_slack_mrkdwn(value: str | None) -> str:
    """Normalize markdown so it renders correctly in Slack."""
    if not value:
        return ""
    normalized = value.replace("\r", "")
    bold_converted = _BOLD_PATTERN.sub(r"*\1*", normalized)
    return _rewrite_links(bold_converted)


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


def create_assistant_response_blocks(payload: AssistantPayload | None) -> list[dict[str, Any]]:
    if not payload:
        return []

    message_id = payload.get("message_id") or payload.get("messageId")
    conversation_id = payload.get("conversation_id") or payload.get("conversationId")
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
            "value": json.dumps({"feedback": 'like', "messageId":  message_id, "conversationId": conversation_id}),
        },
        {
            "type": "button",
            "text": {"type": "plain_text", "text": "👎", "emoji": True},
            "action_id": "dislike_answer",
            "style": "danger",
            "value": json.dumps({"feedback": 'dislike', "messageId":  message_id, "conversationId": conversation_id}),
        },
    ]

    frontend_url = os.getenv("MAGNET_FRONTEND_URL")
    if frontend_url and conversation_id:
        elements.append(
            {
                "type": "button",
                "action_id": "open_conversation",
                "text": {"type": "plain_text", "text": "💬 Open Conversation", "emoji": True},
                "url": f"{frontend_url.rstrip('/')}/#/conversation/{conversation_id}",
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
        reason = data.get("reason") or "other"
        message += f"\nReason: {reason}"
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
        if isinstance(block, dict) and block.get("type") == "actions" and block.get("block_id") == "feedback_actions_block":
            target_index = idx
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
            existing_blocks[target_index] = {
                "type": "actions",
                "elements": filtered,
            }
            existing_blocks.insert(target_index + 1, feedback_context)
        else:
            existing_blocks[target_index] = feedback_context
    else:
        existing_blocks.append(feedback_context)

    return existing_blocks
