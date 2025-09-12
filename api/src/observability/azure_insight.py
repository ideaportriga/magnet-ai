import asyncio
import logging
import os

from opencensus.ext.azure.log_exporter import AzureEventHandler


class SingletonMeta(type):
    """A metaclass for implementing the Singleton pattern."""

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class AzureLogger(metaclass=SingletonMeta):
    """Class for logging events to Azure. Created as a Singleton."""

    def __init__(self):
        self.connection_string = os.getenv("APPINSIGHTS_INSTRUMENTATION_KEY")
        if self.connection_string:
            self.logger = logging.getLogger(__name__)
            self.logger.setLevel(logging.INFO)
            handler = AzureEventHandler(
                connection_string=f"InstrumentationKey={self.connection_string}"
            )
            if not any(isinstance(h, AzureEventHandler) for h in self.logger.handlers):
                self.logger.addHandler(handler)
        else:
            raise ValueError(
                "Environment variable 'APPINSIGHTS_INSTRUMENTATION_KEY' is not set."
            )

    async def log_event(self, event_name, properties=None):
        """Asynchronously logs an event using asyncio to offload to a thread."""
        await asyncio.to_thread(self._log_event_thread, event_name, properties)

    def _log_event_thread(self, event_name, properties=None):
        """Logs an event using multi-threading capabilities."""
        if self.logger:
            if properties:
                custom_dimensions = {"custom_dimensions": properties}
                self.logger.info(event_name, extra=custom_dimensions)
            else:
                self.logger.info(event_name)
        else:
            print("Logger is not initialized properly.")
