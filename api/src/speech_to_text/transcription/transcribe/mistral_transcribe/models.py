from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, List

import httpx

from ...models import TranscriptionCfg
from ...services.ffmpeg import extract_audio_to_wav
from ...storage.postgres_storage import PgDataStorage
from ..base import BaseTranscriber

_MISTRAL_CACHE: dict[str, Dict[str, Any]] = {}

MISTRAL_HTTP_CONNECT_TIMEOUT = 10.0
MISTRAL_HTTP_READ_TIMEOUT = 3600.0
MISTRAL_HTTP_WRITE_TIMEOUT = 60.0
MISTRAL_HTTP_POOL_TIMEOUT = 10.0


def _to_dict(obj: Any):
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


class MistralVoxtralTranscriber(BaseTranscriber):
    def __init__(self, storage: PgDataStorage, cfg: TranscriptionCfg):
        super().__init__(storage, cfg)

        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise RuntimeError("Set MISTRAL_API_KEY")

        base_url = os.getenv("MISTRAL_BASE_URL", "https://api.mistral.ai").rstrip("/")

        self._api_key = api_key
        self._endpoint = f"{base_url}/v1/audio/transcriptions"

        self._http = httpx.Client(
            timeout=httpx.Timeout(
                connect=MISTRAL_HTTP_CONNECT_TIMEOUT,
                read=MISTRAL_HTTP_READ_TIMEOUT,
                write=MISTRAL_HTTP_WRITE_TIMEOUT,
                pool=MISTRAL_HTTP_POOL_TIMEOUT,
                timeout=MISTRAL_HTTP_READ_TIMEOUT,
            )
        )

        self._model = os.getenv("MISTRAL_MODEL_ID") or "voxtral-mini-latest"
        self._language = os.getenv("MISTRAL_LANGUAGE") or None

        # Always ON (your requirement)
        self._diarize = True

        # Required by Mistral when diarize=true
        self._timestamp_granularity = "segment"

    async def _transcribe(self, file_id: str) -> Dict[str, Any]:
        src_url = await self._storage.get_audio_url(file_id)
        tmp_wav = await asyncio.to_thread(
            extract_audio_to_wav, src_path=src_url, sr=16_000
        )

        try:
            try:
                from ...services.ffmpeg import get_wav_duration_seconds

                duration = await asyncio.to_thread(get_wav_duration_seconds, tmp_wav)
                await self._storage._update_fields(
                    file_id, duration_seconds=float(duration)
                )
            except Exception:
                pass

            def _call_http() -> Dict[str, Any]:
                headers = {"Authorization": f"Bearer {self._api_key}"}

                form: Dict[str, str] = {
                    "model": self._model,
                    "diarize": "true",
                    "timestamp_granularities": self._timestamp_granularity,  # "segment"
                }
                if self._language:
                    form["language"] = self._language

                with open(tmp_wav, "rb") as f:
                    files = {"file": ("audio.wav", f, "audio/wav")}
                    r = self._http.post(
                        self._endpoint, headers=headers, data=form, files=files
                    )

                if r.status_code >= 400:
                    raise RuntimeError(f"Mistral error {r.status_code}: {r.text}")

                return r.json()

            raw_payload = await asyncio.to_thread(_call_http)

        finally:
            try:
                os.remove(tmp_wav)
            except OSError:
                pass

        payload = _to_dict(raw_payload) or {}

        segments_out: List[Dict[str, Any]] = []
        segs = _to_dict(payload.get("segments") or []) or []

        for seg in segs:
            seg = _to_dict(seg) or {}
            t = seg.get("text") or seg.get("transcript") or ""
            s = seg.get("start")
            e = seg.get("end", s)
            if s is None or e is None:
                continue
            segments_out.append({"start": float(s), "end": float(e), "text": str(t)})

        text = (
            payload.get("text", "") or " ".join(x["text"] for x in segments_out).strip()
        )

        res = {"text": text, "segments": segments_out}
        _MISTRAL_CACHE[file_id] = {"payload": payload}
        return res


def _drain_cached(file_id: str) -> Dict[str, Any] | None:
    return _MISTRAL_CACHE.pop(file_id, None)
