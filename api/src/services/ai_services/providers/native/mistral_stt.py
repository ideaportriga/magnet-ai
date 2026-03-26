"""
Native Mistral STT Provider for features not supported by LiteLLM.

Mistral Voxtral provides:
- Audio transcription with diarization support
- Language detection
- Speaker identification

This provider calls the Mistral API directly because LiteLLM does not
support Mistral's audio transcription endpoint.

When LiteLLM adds Mistral STT support, this can be replaced with
UniversalLiteLLMProvider (type: "mistral").

Configuration:
    Provider entity:
    {
        "system_name": "mistral-stt",
        "type": "mistral_stt",
        "endpoint": "https://api.mistral.ai",
        "secrets_encrypted": {"api_key": "..."}
    }

    Model entity:
    {
        "system_name": "voxtral-mini",
        "ai_model": "mistral-small-latest",
        "provider_system_name": "mistral-stt",
        "type": "stt"
    }
"""

import asyncio
import logging
from typing import Any, BinaryIO

import requests as req_lib

from services.ai_services.models import TranscriptionResponse
from services.ai_services.providers.native.base import BaseNativeProvider

logger = logging.getLogger(__name__)


class NativeMistralSTTProvider(BaseNativeProvider):
    """
    Native Mistral STT (Voxtral) with diarization support.

    Uses Mistral's /v1/audio/transcriptions endpoint directly.
    Credentials come from the Provider entity in the database.
    """

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        if not self.endpoint:
            self.endpoint = "https://api.mistral.ai"

        # Mistral STT supports long audio — use generous timeout
        self.timeout = self.config.get("connection", {}).get("timeout", 3600)

    async def transcribe(
        self,
        file: BinaryIO,
        model: str | None = None,
        language: str | None = None,
        prompt: str | None = None,
        response_format: str | None = None,
        timestamp_granularities: list[str] | None = None,
        diarize: bool = False,
        **kwargs,
    ) -> TranscriptionResponse:
        """Transcribe audio using Mistral Voxtral."""
        model = model or self.default_model or "mistral-small-latest"

        headers = {"Authorization": f"Bearer {self.api_key}"}

        fields: list[tuple[str, str]] = [("model", model)]
        if language:
            fields.append(("language", language))
        if response_format:
            fields.append(("response_format", response_format))
        # diarize requires timestamp_granularities=segment — enforce it together
        if diarize:
            fields.append(("diarize", "true"))
            for g in timestamp_granularities or ["segment"]:
                fields.append(("timestamp_granularities[]", g))

        filename = getattr(file, "name", "audio.wav")
        file_bytes = file.read()

        url = f"{self.endpoint}/v1/audio/transcriptions"
        logger.warning("[mistral-stt] POST %s model=%s", url, model)

        def _sync_post() -> dict:
            response = req_lib.post(
                url,
                headers=headers,
                data=dict(fields),
                files={"file": (filename, file_bytes, "audio/wav")},
                timeout=self.timeout,
            )
            logger.warning("[mistral-stt] response status=%s", response.status_code)
            if not response.ok:
                raise RuntimeError(
                    f"{response.status_code} {response.reason}: {response.text}"
                )
            return response.json()

        result = await asyncio.to_thread(_sync_post)
        logger.warning(
            "[mistral-stt] transcription text=%r", result.get("text", "")[:100]
        )

        return TranscriptionResponse(
            text=result.get("text", ""),
            language=result.get("language"),
            duration=result.get("duration"),
            segments=result.get("segments"),
            words=result.get("words"),
        )
