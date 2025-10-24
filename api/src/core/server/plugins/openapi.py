"""OpenAPI configuration plugin."""

from typing import TYPE_CHECKING

from litestar.openapi import OpenAPIConfig
from litestar.openapi.plugins import RedocRenderPlugin, StoplightRenderPlugin, SwaggerRenderPlugin
from litestar.openapi.spec import Components, SecurityScheme
from litestar.plugins import InitPluginProtocol

if TYPE_CHECKING:
    from litestar.config.app import AppConfig


class OpenAPIPlugin(InitPluginProtocol):
    """Plugin to configure OpenAPI documentation."""

    def on_app_init(self, app_config: "AppConfig") -> "AppConfig":
        """Configure OpenAPI settings."""
        try:
            from api.tags import get_tags

            openapi_config = OpenAPIConfig(
                title="Magnet AI API",
                version="0.1",  # TODO - retrieve from env variable
                security=[{"ApiKeyAuth": []}],
                tags=get_tags(),
                components=Components(
                    security_schemes={
                        "ApiKeyAuth": SecurityScheme(
                            type="apiKey",
                            security_scheme_in="header",
                            name="x-api-key",
                        ),
                    },
                ),
                # Configure render plugins: Swagger (online), ReDoc and Elements (offline)
                render_plugins=[
                    SwaggerRenderPlugin(),  # Uses default CDN
                    RedocRenderPlugin(
                        js_url="/static/redoc.standalone.js",
                        google_fonts=False,  # Disable Google Fonts for offline mode
                    ),
                    StoplightRenderPlugin(
                        js_url="/static/elements.min.js",
                        css_url="/static/elements.min.css",
                    ),
                ],
            )

            app_config.openapi_config = openapi_config
        except ImportError:
            # Fallback if tags module is not available
            openapi_config = OpenAPIConfig(
                title="Magnet AI API",
                version="0.1",
                security=[{"ApiKeyAuth": []}],
                components=Components(
                    security_schemes={
                        "ApiKeyAuth": SecurityScheme(
                            type="apiKey",
                            security_scheme_in="header",
                            name="x-api-key",
                        ),
                    },
                ),
                # Configure render plugins: Swagger (online), ReDoc and Elements (offline)
                render_plugins=[
                    SwaggerRenderPlugin(),  # Uses default CDN
                    RedocRenderPlugin(
                        js_url="/static/redoc.standalone.js",
                        google_fonts=False,  # Disable Google Fonts for offline mode
                    ),
                    StoplightRenderPlugin(
                        js_url="/static/elements.min.js",
                        css_url="/static/elements.min.css",
                    ),
                ],
            )
            app_config.openapi_config = openapi_config

        return app_config
