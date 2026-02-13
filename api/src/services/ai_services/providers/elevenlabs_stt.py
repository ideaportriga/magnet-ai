from __future__ import annotations

import asyncio
from typing import Any, BinaryIO

import httpx
from elevenlabs.client import ElevenLabs


class ElevenLabsSTTProvider:
    """
    STT-only provider. Not an AIProviderInterface.
    """

    def __init__(self, config: dict[str, Any]):
        conn = config["connection"]
        defaults = config.get("defaults", {})

        api_key = conn.get("api_key")
        if not api_key:
            raise ValueError("ElevenLabs STT provider missing api_key")

        connect = float(conn.get("connect_timeout", 10.0))
        read = float(conn.get("read_timeout", 3600.0))
        write = float(conn.get("write_timeout", 60.0))
        pool = float(conn.get("pool_timeout", 10.0))

        http_client = httpx.Client(
            timeout=httpx.Timeout(
                connect=connect, read=read, write=write, pool=pool, timeout=read
            )
        )
        self._client = ElevenLabs(api_key=api_key, httpx_client=http_client)

        # UI-editable defaults (metadata_info.defaults)
        self.model_default = defaults.get("model_id", "scribe_v2")
        self.diarize_default = bool(defaults.get("diarize", True))
        self.tag_audio_events_default = bool(defaults.get("tag_audio_events", False))
        self.language_code_default = defaults.get("language_code")
        self.num_speakers_default = defaults.get("num_speakers")

    async def speech_to_text_convert(self, *, file: BinaryIO, **kwargs: Any) -> Any:
        def _call():
            return self._client.speech_to_text.convert(file=file, **kwargs)

        return await asyncio.to_thread(_call)
