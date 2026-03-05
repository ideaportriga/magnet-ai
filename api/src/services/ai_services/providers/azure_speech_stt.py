from __future__ import annotations

import json
from typing import Any

import httpx

from services.ai_services.interface import STTProviderInterface


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


class AzureSpeechSTTProvider(STTProviderInterface):
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

        self._client = httpx.AsyncClient()
        self._api_key = api_key
        self._default_diarize = bool(defaults.get("diarize", True))

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

        definition: dict[str, Any] = {}

        # Debug-friendly default: avoid empty definition while you test
        definition["locales"] = [language_code or "en-US"]

        if diarize_final:
            diar: dict[str, Any] = {"enabled": True}
            if num_speakers is not None:
                diar["minSpeakers"] = int(num_speakers)
                diar["maxSpeakers"] = int(num_speakers)
            definition["diarization"] = diar

        if keyterms:
            definition["phraseList"] = {
                "phrases": [
                    {"text": t} for t in keyterms if isinstance(t, str) and t.strip()
                ]
            }

        definition_json = json.dumps(
            definition,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        definition_bytes = definition_json.encode("utf-8")

        resp = await self._client.post(
            self._url,
            headers={"Ocp-Apim-Subscription-Key": self._api_key},
            files={
                "audio": ("audio.wav", file, "audio/wav"),
                "Definition": (
                    None,
                    definition_bytes,
                    "application/json; charset=utf-8",
                ),
            },
        )

        if resp.status_code >= 400:
            raise RuntimeError(f"Azure STT error {resp.status_code}: {resp.text}")

        return _to_dict(resp.json()) or {}
