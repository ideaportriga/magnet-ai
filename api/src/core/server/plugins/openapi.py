"""OpenAPI configuration plugin."""

from pathlib import Path
from typing import TYPE_CHECKING

from litestar.openapi import OpenAPIConfig
from litestar.openapi.plugins import RedocRenderPlugin, StoplightRenderPlugin, SwaggerRenderPlugin
from litestar.openapi.spec import Components, SecurityScheme
from litestar.plugins import InitPluginProtocol

if TYPE_CHECKING:
    from litestar.config.app import AppConfig


# Static files configuration
# The download script saves files to api/static (scripts/download_static_files.py uses
# Path(__file__).parent.parent / "static" -> <repo>/api/static). openapi.py lives in
# api/src/core/server/plugins, so climb 5 parents to reach the api folder.
STATIC_DIR = Path(__file__).parent.parent.parent.parent.parent / "static"
REDOC_LOCAL = STATIC_DIR / "redoc.standalone.js"
ELEMENTS_JS_LOCAL = STATIC_DIR / "elements.min.js"
ELEMENTS_CSS_LOCAL = STATIC_DIR / "elements.min.css"
SWAGGER_JS_LOCAL = STATIC_DIR / "swagger-ui-bundle.js"
SWAGGER_CSS_LOCAL = STATIC_DIR / "swagger-ui.css"
SWAGGER_PRESET_LOCAL = STATIC_DIR / "swagger-ui-standalone-preset.js"

# CDN fallback URLs
REDOC_VERSION = "2.1.3"
ELEMENTS_VERSION = "7.7.18"
SWAGGER_VERSION = "5.18.2"
REDOC_CDN = f"https://cdn.jsdelivr.net/npm/redoc@{REDOC_VERSION}/bundles/redoc.standalone.js"
ELEMENTS_JS_CDN = f"https://unpkg.com/@stoplight/elements@{ELEMENTS_VERSION}/web-components.min.js"
ELEMENTS_CSS_CDN = f"https://unpkg.com/@stoplight/elements@{ELEMENTS_VERSION}/styles.min.css"
SWAGGER_JS_CDN = f"https://cdn.jsdelivr.net/npm/swagger-ui-dist@{SWAGGER_VERSION}/swagger-ui-bundle.js"
SWAGGER_CSS_CDN = f"https://cdn.jsdelivr.net/npm/swagger-ui-dist@{SWAGGER_VERSION}/swagger-ui.css"
SWAGGER_PRESET_CDN = f"https://cdn.jsdelivr.net/npm/swagger-ui-dist@{SWAGGER_VERSION}/swagger-ui-standalone-preset.js"


class OpenAPIPlugin(InitPluginProtocol):
    """Plugin to configure OpenAPI documentation."""

    def on_app_init(self, app_config: "AppConfig") -> "AppConfig":
        """Configure OpenAPI settings."""
        # Determine which URLs to use (local files or CDN fallback)
        redoc_js_url = "/static/redoc.standalone.js" if REDOC_LOCAL.exists() else REDOC_CDN
        elements_js_url = "/static/elements.min.js" if ELEMENTS_JS_LOCAL.exists() else ELEMENTS_JS_CDN
        elements_css_url = "/static/elements.min.css" if ELEMENTS_CSS_LOCAL.exists() else ELEMENTS_CSS_CDN
        swagger_js_url = "/static/swagger-ui-bundle.js" if SWAGGER_JS_LOCAL.exists() else SWAGGER_JS_CDN
        swagger_css_url = "/static/swagger-ui.css" if SWAGGER_CSS_LOCAL.exists() else SWAGGER_CSS_CDN
        swagger_preset_url = "/static/swagger-ui-standalone-preset.js" if SWAGGER_PRESET_LOCAL.exists() else SWAGGER_PRESET_CDN

        # Log which mode is being used
        missing_files = []
        if not REDOC_LOCAL.exists():
            missing_files.append("redoc.standalone.js")
        if not ELEMENTS_JS_LOCAL.exists():
            missing_files.append("elements.min.js")
        if not ELEMENTS_CSS_LOCAL.exists():
            missing_files.append("elements.min.css")
        if not SWAGGER_JS_LOCAL.exists():
            missing_files.append("swagger-ui-bundle.js")
        if not SWAGGER_CSS_LOCAL.exists():
            missing_files.append("swagger-ui.css")
        if not SWAGGER_PRESET_LOCAL.exists():
            missing_files.append("swagger-ui-standalone-preset.js")
        
        if missing_files:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Static files not found: {', '.join(missing_files)}. "
                f"Falling back to CDN. Run 'make download-static' to download them."
            )

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
                # Configure render plugins with automatic fallback to CDN
                render_plugins=[
                    SwaggerRenderPlugin(
                        js_url=swagger_js_url,
                        css_url=swagger_css_url,
                        standalone_preset_js_url=swagger_preset_url,
                    ),
                    RedocRenderPlugin(
                        js_url=redoc_js_url,
                        google_fonts=False,  # Disable Google Fonts for offline mode
                    ),
                    StoplightRenderPlugin(
                        js_url=elements_js_url,
                        css_url=elements_css_url,
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
                # Configure render plugins with automatic fallback to CDN
                render_plugins=[
                    SwaggerRenderPlugin(
                        js_url=swagger_js_url,
                        css_url=swagger_css_url,
                        standalone_preset_js_url=swagger_preset_url,
                    ),
                    RedocRenderPlugin(
                        js_url=redoc_js_url,
                        google_fonts=False,  # Disable Google Fonts for offline mode
                    ),
                    StoplightRenderPlugin(
                        js_url=elements_js_url,
                        css_url=elements_css_url,
                    ),
                ],
            )
            app_config.openapi_config = openapi_config

        return app_config
