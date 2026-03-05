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

import logging
from typing import Any, BinaryIO

import httpx

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
    ) -> TranscriptionResponse:
        """Transcribe audio using Mistral Voxtral with diarization."""
        model = model or self.default_model or "mistral-small-latest"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        # Build form data
        data: dict[str, str] = {
            "model": model,
            "diarize": "true",  # Mistral-specific: enable speaker diarization
        }
        if language:
            data["language"] = language
        if response_format:
            data["response_format"] = response_format

        url = f"{self.endpoint}/v1/audio/transcriptions"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url,
                headers=headers,
                data=data,
                files={"file": file},
            )
            response.raise_for_status()
            result = response.json()

        return TranscriptionResponse(
            text=result.get("text", ""),
            language=result.get("language"),
            duration=result.get("duration"),
            segments=result.get("segments"),
            words=result.get("words"),
        )
