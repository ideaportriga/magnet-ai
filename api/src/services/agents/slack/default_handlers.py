import re
from typing import Callable

from slack_bolt import App

_NON_EMPTY_MESSAGE = re.compile(r"^(?!\s*$).+")


def attach_default_handlers(app: App) -> None:
    @app.event("app_mention")
    def handle_app_mention(event: dict, say: Callable[..., None]) -> None:
        user = event.get("user")
        text = event.get("text", "")
        if user and text:
            say(f"<@{user}> {text}")

    @app.message(_NON_EMPTY_MESSAGE)
    def echo_message(message: dict, say: Callable[..., None]) -> None:
        text = message.get("text", "")
        if text:
            say(text)
