from __future__ import annotations
import os
import asyncio
from typing import Any, Dict
from elevenlabs.client import ElevenLabs


from ..base import BaseTranscriber
from ...storage.postgres_storage import PgDataStorage
from ...models import TranscriptionCfg
from ...services.ffmpeg import extract_audio_to_wav

_ELEVEN_CACHE: dict[str, Dict[str, Any]] = {}


def _to_dict(obj):
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


class ElevenLabsTranscriber(BaseTranscriber):
    def __init__(self, storage: PgDataStorage, cfg: TranscriptionCfg):
        super().__init__(storage, cfg)
        api_key = os.getenv("ELEVENLABS_API_KEY") or os.getenv("ELEVEN_API_KEY")
        if not api_key:
            raise RuntimeError("Set ELEVENLABS_API_KEY")
        self._client = ElevenLabs(api_key=api_key)
        self._model_id = os.getenv("ELEVEN_MODEL_ID", "scribe_v1")
        self._diarize = os.getenv("ELEVEN_DIARIZE", "true").lower() == "true"
        self._language_code = None
        ns = os.getenv("ELEVEN_NUM_SPEAKERS")
        self._num_speakers = int(ns) if ns and ns.isdigit() else None
        self._tag_events = (
            os.getenv("ELEVEN_TAG_AUDIO_EVENTS", "false").lower() == "true"
        )

    async def _transcribe(self, file_id: str) -> Dict[str, Any]:
        src_url = await self._storage.get_audio_url(file_id)

        tmp_wav = await asyncio.to_thread(
            extract_audio_to_wav, src_path=src_url, sr=16_000
        )

        try:

            def _call():
                with open(tmp_wav, "rb") as f:
                    kwargs = dict(
                        file=f,
                        model_id=self._model_id,
                        diarize=self._diarize,
                        tag_audio_events=self._tag_events,
                    )
                    if self._language_code:
                        kwargs["language_code"] = self._language_code

                    return self._client.speech_to_text.convert(**kwargs)

            # 4. Run the API call in a thread
            payload = await asyncio.to_thread(_call)

        finally:
            # 5. Clean up the temp WAV file
            try:
                os.remove(tmp_wav)
            except OSError:
                pass

        # ------------------------------------------------------------------
        # Parsing logic remains the same
        # ------------------------------------------------------------------
        payload = _to_dict(payload) or {}
        words_raw = payload.get("words", []) or []
        words = [_to_dict(w) for w in words_raw]

        segments = []
        for w in words:
            t = w.get("text") or w.get("word") or w.get("value") or ""
            s = w.get("start")
            e = w.get("end", s)
            if s is None or e is None:
                continue
            segments.append(
                {
                    "start": float(s),
                    "end": float(e),
                    "text": t,
                }
            )

        res = {
            "text": payload.get("text", "") or " ".join(x["text"] for x in segments),
            "segments": segments,
        }
        _ELEVEN_CACHE[file_id] = {"payload": payload}
        return res


def _drain_cached(file_id: str) -> Dict[str, Any] | None:
    return _ELEVEN_CACHE.pop(file_id, None)
