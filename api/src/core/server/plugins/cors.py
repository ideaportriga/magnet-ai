"""CORS configuration plugin."""

import os
from typing import TYPE_CHECKING

from litestar.config.cors import CORSConfig
from litestar.plugins import InitPluginProtocol

if TYPE_CHECKING:
    from litestar.config.app import AppConfig


class CORSPlugin(InitPluginProtocol):
    """Plugin to handle CORS configuration."""

    def __init__(self) -> None:
        self.env = os.environ
        self.allowed_origins = self.env.get("CORS_OVERRIDE_ALLOWED_ORIGINS", "").split(
            ","
        )

    def on_app_init(self, app_config: "AppConfig") -> "AppConfig":
        """Configure CORS settings."""
        if self.allowed_origins and self.allowed_origins != [""]:
            cors_config = CORSConfig(
                allow_origins=self.allowed_origins,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
            app_config.cors_config = cors_config

        return app_config
