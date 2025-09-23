"""Oracle monitoring plugin."""

import os
from logging import getLogger
from typing import TYPE_CHECKING

from litestar import Response
from litestar.plugins import InitPluginProtocol

if TYPE_CHECKING:
    from litestar.config.app import AppConfig

logger = getLogger(__name__)


class OracleMonitoringPlugin(InitPluginProtocol):
    """Plugin to add Oracle connection pool monitoring."""

    def __init__(self) -> None:
        self.env = os.environ
        self.db_type = self.env.get("DB_TYPE")

    def on_app_init(self, app_config: "AppConfig") -> "AppConfig":
        """Configure Oracle monitoring if DB_TYPE is ORACLE."""
        # Oracle monitoring will be handled separately in app.py
        # This plugin just provides the monitoring function
        return app_config

    @staticmethod
    async def after_request(response: Response) -> Response:
        """Monitor Oracle connection pool after each request."""
        try:
            from stores import get_db_client
            from stores.oracle.client import OracleDbClient

            client = get_db_client()

            if isinstance(client, OracleDbClient):
                logger.info(
                    f"Oracle connection pool: opened {client._pool.opened}, busy {client._pool.busy}",
                )
        except Exception as e:
            logger.error(f"Error monitoring Oracle connection pool: {e}")

        return response
