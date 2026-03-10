from __future__ import annotations

import asyncio
import os
from io import BytesIO
from typing import Any, Dict

from openai_model.utils import get_model_by_system_name
from services.ai_services.factory import get_ai_provider

from ...models import TranscriptionCfg
from ...services.ffmpeg import extract_audio_to_wav
from ...storage.postgres_storage import PgDataStorage
from ..base import BaseTranscriber


_ELEVEN_CACHE: dict[str, Dict[str, Any]] = {}


def _read_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


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

    cleaned: list[str] = []
    for term in keyterms:
        if not isinstance(term, str):
            continue
        t = term.strip()
        if not t or len(t) > 50:
            continue
        if len(t.split()) > 5:
            t = " ".join(t.split()[:5])
        cleaned.append(t)

    return cleaned[:100]


def _is_provided(x: Any) -> bool:
    if x is None:
        return False
    if isinstance(x, str):
        s = x.strip().lower()
        return s not in ("", "null")
    return True


class ElevenLabsTranscriber(BaseTranscriber):
    def __init__(self, storage: PgDataStorage, cfg: TranscriptionCfg):
        super().__init__(storage, cfg)

        internal = cfg.internal_cfg or {}

        self._model_system_name: str | None = internal.get("model_system_name")
        if not self._model_system_name:
            raise RuntimeError("Missing cfg.internal_cfg['model_system_name']")

        self._language_code = (
            cfg.language.strip() if isinstance(cfg.language, str) else None
        )

        raw_ns = internal.get("num_speakers")
        self._num_speakers: int | None = None
        if _is_provided(raw_ns):
            try:
                ns = int(raw_ns)
                if ns > 0:
                    self._num_speakers = ns
            except (TypeError, ValueError):
                self._num_speakers = None

        raw_thr = internal.get("diarization_threshold")
        self._diarization_threshold: float | None = None
        if _is_provided(raw_thr):
            try:
                thr = float(raw_thr)
                if 0.1 <= thr <= 0.4:
                    self._diarization_threshold = thr
                else:
                    raise ValueError
            except (TypeError, ValueError):
                raise ValueError("diarization_threshold must be in [0.1, 0.4]")

        if self._num_speakers is not None and self._diarization_threshold is not None:
            raise ValueError(
                "Provide either num_speakers OR diarization_threshold, not both."
            )

        diarize_val = internal.get("diarize")
        self._diarize: bool | None = (
            bool(diarize_val) if diarize_val is not None else None
        )

        tag_val = internal.get("tag_audio_events")
        self._tag_events: bool | None = bool(tag_val) if tag_val is not None else None

    async def _transcribe(self, file_id: str) -> Dict[str, Any]:
        src_url = await self._storage.get_audio_url(file_id)

        tmp_wav = await asyncio.to_thread(
            extract_audio_to_wav, src_path=src_url, sr=16_000
        )

        raw_payload: Any = None

        try:
            # Store duration if we can
            try:
                from ...services.ffmpeg import get_wav_duration_seconds

                duration = await asyncio.to_thread(get_wav_duration_seconds, tmp_wav)
                await self._storage._update_fields(
                    file_id, duration_seconds=float(duration)
                )
            except Exception:
                pass

            # Resolve model -> provider + model id
            model_cfg = await get_model_by_system_name(self._model_system_name)
            if not model_cfg:
                raise ValueError(f"STT model '{self._model_system_name}' not found")

            provider_system_name = model_cfg.get("provider_system_name")
            if not isinstance(provider_system_name, str) or not provider_system_name:
                raise ValueError(
                    f"Model '{self._model_system_name}' does not have provider_system_name configured"
                )

            model_id = (
                model_cfg.get("ai_model")
                or model_cfg.get("model_id")
                or model_cfg.get("model")
            )
            if not isinstance(model_id, str) or not model_id:
                raise ValueError(
                    f"Model '{self._model_system_name}' is missing model id"
                )

            provider = await get_ai_provider(provider_system_name)

            safe_terms = _sanitize_keyterms(self._cfg.keyterms or [])
            file_bytes = await asyncio.to_thread(_read_bytes, tmp_wav)

            # Style B: pass advanced STT knobs via model_config
            stt_opts: dict[str, Any] = {
                "diarize": self._diarize,
                "tag_audio_events": self._tag_events,
                "num_speakers": self._num_speakers,
                "diarization_threshold": self._diarization_threshold,
                "keyterms": safe_terms or None,
                "entity_detection": self._cfg.entity_detection,
                # include full model cfg only if your provider uses it
                "model_cfg": model_cfg,
            }

            # NOTE: this requires AIProviderInterface.transcribe to accept model_config
            # and ElevenLabsSTTProvider.transcribe to map model_config -> ElevenLabs kwargs.
            tx = await provider.transcribe(
                file=BytesIO(file_bytes),
                model=model_id,
                language=self._language_code,
                model_config=stt_opts,
            )

            # tx is TranscriptionResponse; keep raw payload for your segment parsing
            raw_payload = getattr(tx, "raw", None) or getattr(tx, "data", None) or tx

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
