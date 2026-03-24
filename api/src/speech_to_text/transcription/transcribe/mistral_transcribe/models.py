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


_MISTRAL_CACHE: dict[str, Dict[str, Any]] = {}


def _read_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


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

        internal = cfg.internal_cfg or {}

        self._model_system_name: str | None = internal.get("model_system_name")
        if not self._model_system_name:
            raise RuntimeError("Missing cfg.internal_cfg['model_system_name']")

        self._language_code = (
            cfg.language.strip() if isinstance(cfg.language, str) else None
        )

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

            file_bytes = await asyncio.to_thread(_read_bytes, tmp_wav)

            stt_opts: dict[str, Any] = {
                "diarize": True,
                "timestamp_granularities": ["segment"],
                "model_cfg": model_cfg,
            }

            if self._cfg.keyterms:
                stt_opts["keyterms"] = self._cfg.keyterms

            tx = await provider.transcribe(
                file=BytesIO(file_bytes),
                model=model_id,
                language=self._language_code,
                model_config=stt_opts,
            )

        finally:
            try:
                os.remove(tmp_wav)
            except OSError:
                pass

        text = tx.text or ""

        segments_raw = tx.segments or []
        segments = []

        for seg in segments_raw:
            s = _to_dict(seg) or {}
            t = s.get("text") or s.get("transcript") or ""
            start = s.get("start")
            end = s.get("end", start)
            if start is None or end is None:
                continue
            segments.append(
                {
                    "start": float(start),
                    "end": float(end),
                    "text": str(t),
                }
            )

        words_raw = tx.words or []
        words = [_to_dict(w) for w in words_raw]

        payload = {
            "text": tx.text,
            "language": tx.language,
            "duration": tx.duration,
            "segments": tx.segments,
            "words": words,
        }

        res = {
            "text": text or " ".join(x["text"] for x in segments).strip(),
            "segments": segments,
        }

        _MISTRAL_CACHE[file_id] = {"payload": payload}
        return res


def _drain_cached(file_id: str) -> Dict[str, Any] | None:
    return _MISTRAL_CACHE.pop(file_id, None)
