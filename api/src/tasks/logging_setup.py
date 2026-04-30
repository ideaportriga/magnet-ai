"""Loki + structlog wiring for TaskIQ CLI / in-process runtimes.

The Litestar `StructlogPlugin` is what attaches the `LokiHandler` and the
structlog ProcessorFormatter to the standard-library root logger. CLI-launched
`taskiq worker` / `taskiq scheduler` processes never go through Litestar, so
without this their log records reach stdout only and never make it to Loki.

For the in-process runtime this is harmless — by the time the worker/scheduler
asyncio tasks spin up the Litestar StructlogPlugin has already wired the root
logger. We still call this from `tasks/broker.py` so the same broker module is
safe to import from a standalone CLI: the handler gets attached idempotently,
and a second invocation (Litestar's own setup) is a no-op because the handler
is already on the root.

Idempotency contract: calling `setup_taskiq_logging()` more than once never
duplicates `LokiHandler` on the root logger, regardless of which order it
runs vs. Litestar's plugin.
"""

from __future__ import annotations

import logging
from logging import getLogger
from typing import Any

logger = getLogger(__name__)


def _has_loki_handler(target: logging.Logger) -> bool:
    return any(
        type(h).__name__ == "LokiHandler" for h in getattr(target, "handlers", [])
    )


def setup_taskiq_logging() -> None:
    """Attach the Loki + structlog stack to the stdlib root logger.

    No-op when:
    - `LOKI_URL` is empty (local dev without Loki).
    - A `LokiHandler` is already attached to the root logger (e.g. Litestar's
      `StructlogPlugin` ran first).

    Failures are logged and swallowed: a missing handler must not stop the
    worker / scheduler from booting.
    """
    try:
        from core.config.base import get_log_settings

        settings = get_log_settings()
        loki_url = settings.LOKI_URL
        if not loki_url:
            return

        root = logging.getLogger()
        if _has_loki_handler(root):
            return

        try:
            import structlog
            from litestar.logging.config import (
                default_structlog_standard_lib_processors,
            )
            from logging_loki import LokiHandler
        except ImportError as exc:
            logger.warning("TaskIQ Loki setup skipped — missing dep: %s", exc)
            return

        processors: list[Any] = default_structlog_standard_lib_processors(as_json=True)
        processors.insert(1, structlog.processors.EventRenamer("message"))
        processors.insert(
            2,
            structlog.processors.CallsiteParameterAdder(
                parameters=[
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.LINENO,
                ]
            ),
        )

        handler = LokiHandler(
            url=loki_url,
            tags={"application": "magnet-ai"},
            version="1",
        )
        formatter = structlog.stdlib.ProcessorFormatter(processors=processors)
        handler.setFormatter(formatter)

        root.addHandler(handler)
        if root.level == logging.NOTSET or root.level > settings.LEVEL:
            root.setLevel(settings.LEVEL)

        # Mirror the small set of Loki-feedback-loop guards from
        # `core/config/app.py`. Without these the LokiHandler emits HTTP
        # logs that turn into more LokiHandler emissions and so on.
        for noisy in ("urllib3", "requests"):
            log = logging.getLogger(noisy)
            log.setLevel(logging.WARNING)
            log.propagate = False

        logger.info("TaskIQ runtime: Loki handler attached (url=%s)", loki_url)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to set up TaskIQ Loki logging: %s", exc)
