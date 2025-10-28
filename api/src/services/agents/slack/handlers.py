import re
from typing import Any

from slack_bolt.async_app import AsyncApp
from slack_bolt.context.say.async_say import AsyncSay
from slack_sdk.web.async_client import AsyncWebClient

_NON_EMPTY_MESSAGE = re.compile(r"^(?!\s*$).+")


def attach_default_handlers(app: AsyncApp) -> None:
    @app.event("app_mention")
    async def handle_app_mention(event: dict[str, Any], say: AsyncSay) -> None:
        user = event.get("user")
        text = event.get("text", "")
        if user and text:
            await say(f"<@{user}> {text}")

    @app.message(_NON_EMPTY_MESSAGE)
    async def echo_message(
        message: dict[str, Any],
        say: AsyncSay,
        context: Any,
        client: AsyncWebClient,
        logger: Any,
    ) -> None:
        tok = context.bot_token or client.token
        logger.info("Using bot token prefix: %s.", (tok or "")[:12])  # TODO: REMOVE IT
        text = message.get("text", "")
        channel = message.get("channel")
        if text and channel:
            await client.chat_postMessage(channel=channel, text=text)
        elif text:
            await say(text)
