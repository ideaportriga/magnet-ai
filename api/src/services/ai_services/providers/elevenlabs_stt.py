from __future__ import annotations

import asyncio
from typing import Any, BinaryIO

import httpx
from elevenlabs.client import ElevenLabs
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam

from services.ai_services.interface import AIProviderInterface
from services.ai_services.models import TranscriptionResponse


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


class ElevenLabsSTTProvider(AIProviderInterface):
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
        self._default_model_id = defaults.get("model_id")

    async def create_chat_completion(
        self,
        messages: list[ChatCompletionMessageParam],
        model: str | None,
        temperature: float | None,
        top_p: float | None,
        max_tokens: int | None = None,
        response_format: dict | None = None,
        tools: list[dict] | None = None,
        tool_choice: str | dict | None = None,
        model_config: dict | None = None,
        parallel_tool_calls: bool | None = None,
    ) -> ChatCompletion:
        raise NotImplementedError(
            "ElevenLabsSTTProvider does not support chat completions"
        )

    async def transcribe(
        self,
        file: BinaryIO,
        model: str | None = None,
        language: str | None = None,
        prompt: str | None = None,
        response_format: str | None = None,
        timestamp_granularities: list[str] | None = None,
        model_config: dict[str, Any] | None = None,
    ) -> TranscriptionResponse:
        model_config = model_config or {}
        audio_bytes = file.read()

        model_id = model or model_config.get("model_id") or self._default_model_id
        if not model_id:
            raise ValueError(
                "ElevenLabs transcribe: model_id is required "
                "(pass model=..., or model_config['model_id'], or set defaults.model_id)"
            )

        diarize_final = (
            self._default_diarize
            if model_config.get("diarize") is None
            else bool(model_config.get("diarize"))
        )
        tag_final = (
            self._default_tag_events
            if model_config.get("tag_audio_events") is None
            else bool(model_config.get("tag_audio_events"))
        )

        kwargs: dict[str, Any] = {
            "file": audio_bytes,
            "model_id": model_id,
            "diarize": diarize_final,
            "tag_audio_events": tag_final,
        }

        if language:
            kwargs["language_code"] = language

        if model_config.get("keyterms"):
            kwargs["keyterms"] = model_config["keyterms"]

        if model_config.get("entity_detection"):
            kwargs["entity_detection"] = model_config["entity_detection"]

        if model_config.get("num_speakers") is not None:
            kwargs["num_speakers"] = int(model_config["num_speakers"])

        if model_config.get("diarization_threshold") is not None:
            kwargs["diarization_threshold"] = float(
                model_config["diarization_threshold"]
            )

        def _call():
            return self._client.speech_to_text.convert(**kwargs)

        raw = await asyncio.to_thread(_call)
        payload = _to_dict(raw) or {}

        text = payload.get("text") or payload.get("transcript") or ""

        segments = payload.get("segments")
        if not isinstance(segments, list):
            segments = None

        words = payload.get("words")
        if not isinstance(words, list):
            words = None

        return TranscriptionResponse(
            text=text,
            language=payload.get("language_code") or payload.get("language"),
            duration=payload.get("duration"),
            segments=segments,
            words=words,
        )
