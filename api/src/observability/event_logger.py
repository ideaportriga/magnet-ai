import os

import structlog

from observability.azure_insight import AzureLogger

logger = structlog.get_logger(__name__)
env = os.environ


def get_default_properties():
    return {
        "app": "magnetui",
        "env": env.get("ENV", "local"),
        "user_id": "test-user-id",
    }


class EventLogger:
    def __init__(self, logger=None):
        try:
            # Use AzureLogger by default if another logger is not provided
            self.logger = logger if logger else AzureLogger()
        except Exception:
            print("Failed to initialize EventLogger")

    async def log_event(self, event_name, properties=None):
        try:
            if self.logger is None:
                print("Logger is not initialized properly.")
                return
            # Retrieve default properties
            default_properties = get_default_properties()
            # Merge default properties with user-provided properties
            combined_properties = {
                **default_properties,
                **(properties if properties else {}),
            }

            # Log the event asynchronously
            await self.logger.log_event(event_name, combined_properties)
        except Exception as e:
            # Log the exception to avoid losing information about the error
            logger.error(f"Failed to log event: {event_name}. Error: {e}")
