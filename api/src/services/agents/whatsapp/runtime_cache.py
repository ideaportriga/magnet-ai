import asyncio
from logging import getLogger
from typing import Dict

from .config import load_credentials
from .runtime import WhatsappRuntime


logger = getLogger(__name__)


class WhatsappRuntimeCache:
    """Runtimes keyed by WhatsApp phone_number_id."""

    def __init__(self) -> None:
        self._runtimes: Dict[str, WhatsappRuntime] = {}
        self._lock = asyncio.Lock()

    async def get_or_create(self, phone_number_id: str) -> WhatsappRuntime:
        async with self._lock:
            runtime = self._runtimes.get(phone_number_id)
            if runtime is not None:
                return runtime

            runtime = await self._build_runtime(phone_number_id)
            self._runtimes[phone_number_id] = runtime
            logger.info(
                "Initialized WhatsApp runtime for phone_number_id=%s agent=%s",
                phone_number_id,
                runtime.agent_system_name,
            )
            return runtime

    async def _build_runtime(self, phone_number_id: str) -> WhatsappRuntime:
        credentials = await load_credentials(phone_number_id)
        return WhatsappRuntime(
            phone_number_id=credentials.phone_number_id,
            agent_system_name=credentials.agent_system_name,
            token=credentials.token,
            app_secret=credentials.app_secret,
        )

    async def clear(self) -> None:
        async with self._lock:
            removed = len(self._runtimes)
            self._runtimes.clear()

        logger.info("WhatsApp runtime cache cleared (removed %d runtime(s))", removed)
