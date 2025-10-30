import asyncio
from logging import getLogger
from typing import Any, Dict, Iterable
import json

from .runtime import SlackRuntime, discover_bots_from_db


logger = getLogger(__name__)


class SlackRuntimeCache:
    """In-memory cache of Slack runtimes keyed by agent name."""

    def __init__(self) -> None:
        self._bots: Dict[str, SlackRuntime] = {}
        self._lock = asyncio.Lock()

    async def load(self) -> None:
        """Load all Slack runtimes from the database."""
        bots = await discover_bots_from_db()
        mapping: Dict[str, SlackRuntime] = {}
        duplicates: set[str] = set()

        for bot in bots:
            if not bot.name:
                logger.warning("Skipping Slack bot with empty name during cache load")
                continue

            if bot.name in mapping:
                duplicates.add(bot.name)
            mapping[bot.name] = bot

        async with self._lock:
            self._bots = mapping

        logger.info(
            "Slack runtime cache loaded %d bot(s)%s",
            len(mapping),
            f" (duplicate names: {', '.join(sorted(duplicates))})" if duplicates else "",
        )

    async def refresh(self) -> None:
        """Reload runtimes from the database."""
        await self.load()

    def get(self, name: str) -> SlackRuntime | None:
        """Return the runtime for the given agent name, if available."""
        return self._bots.get(name)

    def all(self) -> Iterable[SlackRuntime]:
        """Return an iterable with the cached runtimes."""
        return list(self._bots.values())

    def find(self, raw_body: bytes | str | dict[str, Any], headers: dict[str, str]) -> SlackRuntime | None:
        """Try each agent's signing secret to find the correct one.

        Slack signature verification requires the exact raw request body as a string
        and the canonical Slack headers. We normalize both here.
        """

        # Normalize body to a string exactly as sent by Slack when possible
        if isinstance(raw_body, bytes):
            body_text = raw_body.decode("utf-8")
        elif isinstance(raw_body, str):
            body_text = raw_body
        else:
            try:
                body_text = json.dumps(raw_body, separators=(",", ":"))
            except Exception:
                body_text = str(raw_body)

        # Normalize header keys for Slack SDK
        canonical_headers: dict[str, str] = {}
        for key, value in headers.items():
            canonical_headers[str(key)] = str(value)
        signature = None
        timestamp = None
        for key, value in headers.items():
            lower_key = str(key).lower()
            if lower_key == "x-slack-signature":
                signature = str(value)
            elif lower_key == "x-slack-request-timestamp":
                timestamp = str(value)
        if signature is not None:
            canonical_headers["X-Slack-Signature"] = signature
        if timestamp is not None:
            canonical_headers["X-Slack-Request-Timestamp"] = timestamp

        for runtime in self.all():
            logger.info(">>> Checking agent %s", runtime.name)
            if runtime.verifier.is_valid_request(body_text, canonical_headers):
                logger.info("Slack agent found: %s", runtime.name)
                return runtime
        logger.info("No Slack agent found")
        return None


    async def clear(self) -> None:
        async with self._lock:
            removed = len(self._bots)
            self._bots.clear()

        logger.info("Slack runtime cache cleared (removed %d bot(s))", removed)


    @property
    def count(self) -> int:
        return len(self._bots)
