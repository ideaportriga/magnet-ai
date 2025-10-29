import logging
from typing import Any

from services.agents.slack.blocks import build_welcome_message_blocks
from slack_sdk.errors import SlackApiError
from slack_sdk.oauth.installation_store.models import Installation
from slack_sdk.web.async_client import AsyncWebClient
from services.agents.utils.conversation_helpers import DEFAULT_AGENT_DISPLAY_NAME

logger = logging.getLogger(__name__)


def _extract_installer_user_id(installation: Installation) -> str | None:
    candidates: list[Any] = [
        getattr(installation, "user_id", None),
        getattr(installation, "installer_user_id", None),
        getattr(installation, "installer_user", None),
    ]
    custom_values = getattr(installation, "custom_values", None) or {}
    if isinstance(custom_values, dict):
        for key in (
            "installer_user_id",
            "installerUserId",
            "installer_user",
            "installerUser",
            "user_id",
            "userId",
        ):
            candidates.append(custom_values.get(key))

    for candidate in candidates:
        if isinstance(candidate, str):
            trimmed = candidate.strip()
            if trimmed:
                return trimmed
    return None


async def _fetch_bot_display_name(client: AsyncWebClient, bot_user_id: str | None) -> str | None:
    if not bot_user_id:
        return None

    try:
        response = await client.users_info(user=bot_user_id)
    except SlackApiError as exc:
        logger.warning("Failed to fetch bot profile for %s: %s", bot_user_id, exc)
        return None

    user = response.get("user") or {}
    profile = user.get("profile") or {}
    return (
        profile.get("display_name")
        or profile.get("real_name")
        or user.get("name")
        or None
    )


async def send_installation_welcome_message(
    installation: Installation,
    agent_display_name: str,
) -> None:

    bot_token = getattr(installation, "bot_token", None)
    bot_user_id = getattr(installation, "bot_user_id", None)
    installer_user_id = _extract_installer_user_id(installation)

    if not bot_token or not installer_user_id:
        logger.debug(
            "Skipping welcome DM (bot_token=%s installer_user_id=%s)",
            "present" if bot_token else "missing",
            installer_user_id or "<missing>",
        )
        return

    client = AsyncWebClient(token=bot_token)
    try:
        bot_name = await _fetch_bot_display_name(client, bot_user_id)
        display_name = bot_name or DEFAULT_AGENT_DISPLAY_NAME

        try:
            open_response = await client.conversations_open(users=installer_user_id)
        except SlackApiError as exc:
            logger.error("Failed to open DM channel with %s: %s", installer_user_id, exc)
            return

        channel_id = (open_response.get("channel") or {}).get("id")
        if not channel_id:
            logger.error("No conversation ID returned when opening DM with %s", installer_user_id)
            return

        blocks, message_text = build_welcome_message_blocks(display_name, agent_display_name)

        await client.chat_postMessage(
            channel=channel_id,
            text=message_text,
            blocks=blocks,
        )
    except Exception:
        logger.exception("Failed to send post-install welcome DM")
    finally:
        await client.close()
