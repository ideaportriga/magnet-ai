"""Process-local NoteTakerRegistry singleton for taskiq workers.

The webhook handler enqueues per-notification background tasks; the worker
process doesn't share ``app.state`` with the API, so it builds its own
registry on first use and caches it for the lifetime of the process.

Hot-reload of provider credentials is not currently supported in the
worker — restart the worker if you've rotated bot secrets.
"""

from __future__ import annotations

import asyncio
from logging import getLogger
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .note_taker import NoteTakerRegistry

logger = getLogger(__name__)

_registry: "NoteTakerRegistry | None" = None
_lock = asyncio.Lock()


async def get_worker_registry() -> "NoteTakerRegistry":
    """Return (lazily building) the registry shared across worker tasks."""
    global _registry
    if _registry is not None:
        return _registry
    async with _lock:
        if _registry is not None:
            return _registry
        from .note_taker import NoteTakerRegistry

        registry = NoteTakerRegistry()
        loaded = await registry.load_all_from_db()
        logger.info(
            "[note-taker worker] Loaded %d note-taker runtime(s) for background processing.",
            loaded,
        )
        _registry = registry
        return _registry


async def reset_for_tests() -> None:
    global _registry
    async with _lock:
        _registry = None
