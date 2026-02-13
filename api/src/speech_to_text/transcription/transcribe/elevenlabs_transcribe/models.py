from __future__ import annotations

import asyncio
import os
from typing import Any, Dict

import httpx
from elevenlabs.client import ElevenLabs

from ...models import TranscriptionCfg
from ...services.ffmpeg import extract_audio_to_wav
from ...storage.postgres_storage import PgDataStorage
from ..base import BaseTranscriber

_ELEVEN_CACHE: dict[str, Dict[str, Any]] = {}

# ────────────────────────────────
# ElevenLabs / HTTP timeouts (seconds)
# ────────────────────────────────
ELEVEN_HTTP_CONNECT_TIMEOUT = 10.0
ELEVEN_HTTP_READ_TIMEOUT = 3600.0  # 1h
ELEVEN_HTTP_WRITE_TIMEOUT = 60.0
ELEVEN_HTTP_POOL_TIMEOUT = 10.0


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


def _sanitize_keyterms(keyterms: list[str]) -> list[str]:
    if not keyterms:
        return []

    cleaned = []
    for term in keyterms:
        # skip non-string or empty
        if not isinstance(term, str):
            continue
        t = term.strip()
        # skip too long strings
        if not t or len(t) > 50:
            continue
        # limit to 5 words
        if len(t.split()) > 5:
            t = " ".join(t.split()[:5])
        cleaned.append(t)

    return cleaned[:100]


class ElevenLabsTranscriber(BaseTranscriber):
    def __init__(self, storage: PgDataStorage, cfg: TranscriptionCfg):
        super().__init__(storage, cfg)

        api_key = os.getenv("ELEVENLABS_API_KEY") or os.getenv("ELEVEN_API_KEY")
        if not api_key:
            raise RuntimeError("Set ELEVENLABS_API_KEY")

        http_client = httpx.Client(
            timeout=httpx.Timeout(
                connect=ELEVEN_HTTP_CONNECT_TIMEOUT,
                read=ELEVEN_HTTP_READ_TIMEOUT,
                write=ELEVEN_HTTP_WRITE_TIMEOUT,
                pool=ELEVEN_HTTP_POOL_TIMEOUT,
                timeout=ELEVEN_HTTP_READ_TIMEOUT,
            )
        )

        self._client = ElevenLabs(
            api_key=api_key,
            httpx_client=http_client,
        )

        self._model_id = os.getenv("ELEVEN_MODEL_ID", "scribe_v2")
        self._diarize = os.getenv("ELEVEN_DIARIZE", "true").lower() == "true"
        self._tag_events = (
            os.getenv("ELEVEN_TAG_AUDIO_EVENTS", "false").lower() == "true"
        )

        self._language_code = None

        self._num_speakers = None
        internal = cfg.internal_cfg or {}

        raw_ns = internal.get("num_speakers")
        if raw_ns is not None:
            try:
                ns_int = int(raw_ns)
                if ns_int > 0:
                    self._num_speakers = ns_int
            except (TypeError, ValueError):
                self._num_speakers = None

    async def _transcribe(self, file_id: str) -> Dict[str, Any]:
        src_url = await self._storage.get_audio_url(file_id)

        tmp_wav = await asyncio.to_thread(
            extract_audio_to_wav, src_path=src_url, sr=16_000
        )

        raw_payload = None

        try:
            try:
                from ...services.ffmpeg import (
                    get_wav_duration_seconds,
                )

                duration = await asyncio.to_thread(get_wav_duration_seconds, tmp_wav)
                await self._storage._update_fields(
                    file_id, duration_seconds=float(duration)
                )
            except Exception:
                pass

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
                    safe_terms = _sanitize_keyterms(self._cfg.keyterms)
                    if safe_terms:
                        kwargs["keyterms"] = safe_terms
                    if self._cfg.entity_detection:
                        kwargs["entity_detection"] = self._cfg.entity_detection
                    if self._num_speakers is not None:
                        kwargs["num_speakers"] = self._num_speakers

                    return self._client.speech_to_text.convert(**kwargs)

            raw_payload = await asyncio.to_thread(_call)

        finally:
            try:
                os.remove(tmp_wav)
            except OSError:
                pass

        payload = _to_dict(raw_payload) or {}
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
