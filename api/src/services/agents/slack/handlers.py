import re

from slack_bolt import App
from slack_bolt.context.say import Say

_NON_EMPTY_MESSAGE = re.compile(r"^(?!\s*$).+")


def attach_default_handlers(app: App) -> None:
    @app.event("app_mention")
    def handle_app_mention(event: dict, say: Say) -> None:
        user = event.get("user")
        text = event.get("text", "")
        if user and text:
            say(f"<@{user}> {text}")

    @app.message(_NON_EMPTY_MESSAGE)
    def echo_message(message: dict, say: Say, context, client, logger) -> None:
        tok = context.bot_token or client.token
        logger.info("Using bot token prefix: %s…", (tok or "")[:12]) # TODO: REMOVE IT
        text = message.get("text", "")
        if text:
            say(text)
