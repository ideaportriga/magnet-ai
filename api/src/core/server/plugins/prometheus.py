"""Prometheus metrics endpoint plugin.

Exposes a single scrape endpoint (``OBSERVABILITY_PROMETHEUS_PATH``, default
``/metrics``) that serves:

* HTTP request metrics produced by Litestar's Prometheus middleware, and
* the existing OpenTelemetry GenAI metrics (duration / tokens / cost), which are
  registered on prometheus_client's default registry by the
  ``PrometheusMetricReader`` wired up in ``otel/config/utils.py``.

The endpoint is marked ``exclude_from_auth`` so Prometheus scrapers can reach it
even when application auth is enabled. Restrict access at the network layer
(scrape from inside the cluster / behind an IP allowlist).
"""

from typing import TYPE_CHECKING

from litestar.plugins import InitPluginProtocol

from core.config.base import get_observability_settings

if TYPE_CHECKING:
    from litestar.config.app import AppConfig


class PrometheusPlugin(InitPluginProtocol):
    """Wire up the Prometheus middleware + scrape endpoint when enabled."""

    def on_app_init(self, app_config: "AppConfig") -> "AppConfig":
        settings = get_observability_settings()
        if not (settings.ENABLED and settings.PROMETHEUS_ENABLED):
            return app_config

        from litestar.plugins.prometheus import PrometheusConfig, PrometheusController

        prometheus_config = PrometheusConfig(app_name="magnet_ai")

        class MetricsController(PrometheusController):
            path = settings.PROMETHEUS_PATH
            # Allow scrapers through the auth middleware (see middlewares/auth.py).
            opt = {"exclude_from_auth": True}

        app_config.route_handlers.append(MetricsController)
        existing_middleware = list(app_config.middleware or [])
        app_config.middleware = existing_middleware + [prometheus_config.middleware]

        return app_config
