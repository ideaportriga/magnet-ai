from __future__ import annotations

import json
from typing import Any, BinaryIO

import httpx
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam

from services.ai_services.interface import AIProviderInterface
from services.ai_services.models import TranscriptionResponse


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


class AzureSpeechSTTProvider(AIProviderInterface):
    def __init__(self, cfg: dict[str, Any]):
        self._cfg = cfg
        connection = cfg.get("connection", {}) or {}
        defaults = cfg.get("defaults", {}) or {}

        api_key = (
            connection.get("api_key")
            or connection.get("AZURE_SPEECH_KEY")
            or connection.get("SPEECH_KEY")
        )
        if not api_key:
            raise RuntimeError(
                "AzureSpeech provider: missing api_key in provider connection"
            )

        endpoint = (connection.get("endpoint") or "").strip()
        region = (
            connection.get("region")
            or connection.get("AZURE_SPEECH_REGION")
            or connection.get("SPEECH_REGION")
            or ""
        ).strip()

        if endpoint:
            base = endpoint.rstrip("/")
        elif region:
            base = f"https://{region}.api.cognitive.microsoft.com"
        else:
            raise RuntimeError(
                "AzureSpeech provider: missing region or endpoint in provider connection"
            )

        self._url = (
            f"{base}/speechtotext/transcriptions:transcribe?api-version=2025-10-15"
        )

        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=15.0,
                write=2400.0,
                read=300.0,
                pool=30.0,
            )
        )
        self._api_key = api_key
        self._default_diarize = bool(defaults.get("diarize", True))

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
            "AzureSpeechSTTProvider does not support chat completions"
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

        diarize_final = (
            self._default_diarize
            if model_config.get("diarize") is None
            else bool(model_config.get("diarize"))
        )

        definition: dict[str, Any] = {
            "locales": [language or "en-US"],
        }

        diarize_final = True

        definition: dict[str, Any] = {
            "locales": [language or "en-US"],
            "diarization": {
                "enabled": diarize_final,
            },
        }

        definition["diarization"]["minSpeakers"] = 2
        definition["diarization"]["maxSpeakers"] = 2

        if model_config.get("keyterms"):
            definition["phraseList"] = {
                "phrases": [
                    {"text": t}
                    for t in model_config["keyterms"]
                    if isinstance(t, str) and t.strip()
                ]
            }

        definition_json = json.dumps(
            definition,
            ensure_ascii=False,
            separators=(",", ":"),  # compact is fine
        )

        # Better: use httpx multipart form with explicit Content-Type for definition
        files = {
            "definition": (
                "definition.json",  # filename can help Azure parse it
                definition_json.encode("utf-8"),  # ensure bytes + utf-8
                "application/json",  # ← important!
            ),
            "audio": (
                "audio.wav",  # use original extension if possible (m4a, wav, mp3 all ok)
                audio_bytes,
                "audio/wav",  # or "audio/wav" etc. — match what you have
            ),
        }

        headers = {
            "Ocp-Apim-Subscription-Key": self._api_key,
            # You can add Accept: application/json if you want, but usually not needed
        }

        resp = await self._client.post(
            self._url,
            headers=headers,
            files=files,  # ← no data= dict anymore
        )

        if resp.status_code >= 400:
            raise RuntimeError(f"Azure STT error {resp.status_code}: {resp.text}")

        payload = _to_dict(resp.json()) or {}

        # Preserve Azure-native phrase structures so downstream diarization can use them
        segments = None
        if isinstance(payload.get("phrases"), list):
            segments = payload["phrases"]
        elif isinstance(payload.get("recognizedPhrases"), list):
            segments = payload["recognizedPhrases"]

        text = ""
        combined = payload.get("combinedPhrases")
        if isinstance(combined, list) and combined:
            text = combined[0].get("text") or combined[0].get("display") or ""

        if not text and isinstance(payload.get("phrases"), list):
            text = " ".join(
                (p.get("text") or p.get("display") or "").strip()
                for p in payload["phrases"]
                if isinstance(p, dict)
            ).strip()

        if not text and isinstance(payload.get("recognizedPhrases"), list):
            text = " ".join(
                (
                    p.get("nBest", [{}])[0].get("display") or p.get("display") or ""
                ).strip()
                for p in payload["recognizedPhrases"]
                if isinstance(p, dict)
            ).strip()

        duration = None
        if payload.get("durationMilliseconds") is not None:
            try:
                duration = float(payload["durationMilliseconds"]) / 1000.0
            except Exception:
                duration = None
        print(
            "definition sent:",
            json.dumps(definition, ensure_ascii=True, separators=(",", ":")),
        )
        print(
            "first phrases:",
            json.dumps((payload.get("phrases") or [])[:3], ensure_ascii=False),
        )

        return TranscriptionResponse(
            text=text,
            language=language,
            duration=duration,
            segments=segments,
        )
