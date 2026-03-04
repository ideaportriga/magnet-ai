from __future__ import annotations

import asyncio
from typing import Any

import httpx
from elevenlabs.client import ElevenLabs

from ..interface import STTProviderInterface


ELEVEN_HTTP_CONNECT_TIMEOUT = 10.0
ELEVEN_HTTP_READ_TIMEOUT = 3600.0
ELEVEN_HTTP_WRITE_TIMEOUT = 60.0
ELEVEN_HTTP_POOL_TIMEOUT = 10.0


def _to_dict(obj: Any) -> Any:
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    if isinstance(obj, (list, tuple)):
        return [_to_dict(x) for x in obj]
    if hasattr(obj, "json"):
        import json as _json

        try:
            return _json.loads(obj.json())
        except Exception:
            pass
    return obj


class ElevenLabsSTTProvider(STTProviderInterface):
    def __init__(self, cfg: dict[str, Any]):
        self._cfg = cfg
        connection = cfg.get("connection", {}) or {}
        defaults = cfg.get("defaults", {}) or {}

        api_key = (
            connection.get("api_key")
            or connection.get("ELEVENLABS_API_KEY")
            or connection.get("ELEVEN_API_KEY")
        )
        if not api_key:
            raise RuntimeError(
                "ElevenLabs provider: missing api_key in provider connection"
            )

        timeout_s = float(connection.get("timeout", ELEVEN_HTTP_READ_TIMEOUT))

        http_client = httpx.Client(
            timeout=httpx.Timeout(
                connect=float(
                    connection.get("connect_timeout", ELEVEN_HTTP_CONNECT_TIMEOUT)
                ),
                read=timeout_s,
                write=float(connection.get("write_timeout", ELEVEN_HTTP_WRITE_TIMEOUT)),
                pool=float(connection.get("pool_timeout", ELEVEN_HTTP_POOL_TIMEOUT)),
                timeout=timeout_s,
            )
        )

        self._client = ElevenLabs(api_key=api_key, httpx_client=http_client)

        self._default_diarize = bool(defaults.get("diarize", True))
        self._default_tag_events = bool(defaults.get("tag_audio_events", False))

    async def speech_to_text_convert(
        self,
        *,
        file: bytes,
        model_id: str,
        diarize: bool | None = None,
        tag_audio_events: bool | None = None,
        language_code: str | None = None,
        num_speakers: int | None = None,
        diarization_threshold: float | None = None,
        keyterms: list[str] | None = None,
        entity_detection: str | list[str] | None = None,
        model_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        diarize_final = self._default_diarize if diarize is None else bool(diarize)
        tag_final = (
            self._default_tag_events
            if tag_audio_events is None
            else bool(tag_audio_events)
        )

        kwargs: dict[str, Any] = {
            "file": file,
            "model_id": model_id,
            "diarize": diarize_final,
            "tag_audio_events": tag_final,
        }
        if language_code:
            kwargs["language_code"] = language_code
        if keyterms:
            kwargs["keyterms"] = keyterms
        if entity_detection:
            kwargs["entity_detection"] = entity_detection
        if num_speakers is not None:
            kwargs["num_speakers"] = int(num_speakers)
        if diarization_threshold is not None:
            kwargs["diarization_threshold"] = float(diarization_threshold)

        def _call():
            return self._client.speech_to_text.convert(**kwargs)

        raw = await asyncio.to_thread(_call)
        payload = _to_dict(raw) or {}
        return payload
