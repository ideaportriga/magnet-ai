from __future__ import annotations

from typing import Any, BinaryIO

import httpx
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam

from services.ai_services.models import TranscriptionResponse
from services.ai_services.providers.native.base import BaseNativeProvider


MISTRAL_HTTP_CONNECT_TIMEOUT = 10.0
MISTRAL_HTTP_READ_TIMEOUT = 3600.0
MISTRAL_HTTP_WRITE_TIMEOUT = 60.0
MISTRAL_HTTP_POOL_TIMEOUT = 10.0


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


class NativeMistralSTTProvider(BaseNativeProvider):
    def __init__(self, cfg: dict[str, Any]):
        super().__init__(cfg)

        connection = cfg.get("connection", {}) or {}
        defaults = cfg.get("defaults", {}) or {}

        self.api_key = self.api_key or connection.get("MISTRAL_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "Mistral provider: missing api_key in provider connection"
            )

        self.endpoint = str(self.endpoint or "https://api.mistral.ai").rstrip("/")

        timeout_s = float(connection.get("timeout", MISTRAL_HTTP_READ_TIMEOUT))
        self._timeout = httpx.Timeout(
            connect=float(
                connection.get("connect_timeout", MISTRAL_HTTP_CONNECT_TIMEOUT)
            ),
            read=timeout_s,
            write=float(connection.get("write_timeout", MISTRAL_HTTP_WRITE_TIMEOUT)),
            pool=float(connection.get("pool_timeout", MISTRAL_HTTP_POOL_TIMEOUT)),
            timeout=timeout_s,
        )

        self._default_diarize = bool(defaults.get("diarize", True))
        self._default_model_id = self.default_model or "voxtral-mini-latest"

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
            "NativeMistralSTTProvider does not support chat completions"
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
                "Mistral transcribe: model_id is required "
                "(pass model=..., or model_config['model_id'], or set defaults.model)"
            )

        diarize_final = (
            self._default_diarize
            if model_config.get("diarize") is None
            else bool(model_config.get("diarize"))
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        data: dict[str, Any] = {
            "model": model_id,
            "diarize": str(diarize_final).lower(),
        }

        if language:
            data["language"] = language

        if prompt:
            data["prompt"] = prompt

        if response_format:
            data["response_format"] = response_format

        timestamps = (
            timestamp_granularities
            if timestamp_granularities is not None
            else model_config.get("timestamp_granularities")
        )

        if timestamps:
            data["timestamp_granularities"] = timestamps
        elif language:
            data["language"] = language

        context_bias = model_config.get("context_bias") or model_config.get("keyterms")
        if context_bias:
            data["context_bias"] = context_bias

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self.endpoint}/v1/audio/transcriptions",
                headers=headers,
                data=data,
                files={"file": ("audio.wav", audio_bytes)},
            )
            if response.status_code >= 400:
                raise RuntimeError(
                    f"Mistral error {response.status_code}: {response.text}"
                )
            response.raise_for_status()
            payload = _to_dict(response.json()) or {}

        text = payload.get("text") or payload.get("transcript") or ""

        segments = payload.get("segments")
        if not isinstance(segments, list):
            segments = None

        words = payload.get("words")
        if not isinstance(words, list):
            words = None

        return TranscriptionResponse(
            text=text,
            language=payload.get("language"),
            duration=payload.get("duration"),
            segments=segments,
            words=words,
        )
