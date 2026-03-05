from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, List

from ...models import TranscriptionCfg
from ...services.ffmpeg import extract_audio_to_wav
from ...storage.postgres_storage import PgDataStorage
from ..base import BaseTranscriber

from services.ai_services.utils import get_stt_provider_by_model


_AZURE_CACHE: dict[str, Dict[str, Any]] = {}


def _put_cached(file_id: str, payload: Dict[str, Any]) -> None:
    _AZURE_CACHE[file_id] = {"payload": payload}


def _drain_cached(file_id: str) -> Dict[str, Any] | None:
    return _AZURE_CACHE.pop(file_id, None)


def _read_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


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


def _sanitize_keyterms(keyterms: list[str] | None) -> list[str]:
    if not keyterms:
        return []
    cleaned = []
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


def _ms_to_s(x: Any) -> float:
    try:
        return float(x or 0.0) / 1000.0
    except Exception:
        return 0.0


def _get_phrase_text(p: Dict[str, Any]) -> str:
    return (
        p.get("text")
        or p.get("display")
        or p.get("lexical")
        or p.get("itn")
        or p.get("maskedITN")
        or ""
    )


def _azure_payload_to_segments(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    segs: list[dict[str, Any]] = []

    phrases = payload.get("phrases")
    if isinstance(phrases, list) and phrases:
        try:
            phrases = sorted(
                phrases, key=lambda p: _ms_to_s(p.get("offsetMilliseconds"))
            )
        except Exception:
            pass

        for p in phrases:
            s = _ms_to_s(p.get("offsetMilliseconds"))
            e = s + _ms_to_s(p.get("durationMilliseconds"))
            txt = _get_phrase_text(p).strip()
            if txt and e >= s:
                segs.append({"start": float(s), "end": float(e), "text": txt})
        return segs

    rp = payload.get("recognizedPhrases") or payload.get("recognitionResult", {}).get(
        "recognizedPhrases"
    )
    if isinstance(rp, list) and rp:

        def ticks_to_s(t: Any) -> float:
            try:
                return float(t or 0.0) / 10_000_000.0
            except Exception:
                return 0.0

        try:
            rp = sorted(
                rp, key=lambda p: ticks_to_s(p.get("offset") or p.get("offsetInTicks"))
            )
        except Exception:
            pass

        for p in rp:
            off = p.get("offset") or p.get("offsetInTicks") or 0
            dur = p.get("duration") or p.get("durationInTicks") or 0
            s = ticks_to_s(off)
            e = s + ticks_to_s(dur)
            txt = (
                p.get("nBest", [{}])[0].get("display")
                or p.get("nBest", [{}])[0].get("lexical")
                or p.get("display")
                or p.get("lexical")
                or ""
            )
            txt = str(txt).strip()
            if txt and e >= s:
                segs.append({"start": float(s), "end": float(e), "text": txt})

    return segs


def _azure_payload_to_text(
    payload: Dict[str, Any], segments: List[Dict[str, Any]]
) -> str:
    cp = payload.get("combinedPhrases")
    if isinstance(cp, list) and cp:
        txt = cp[0].get("text") or cp[0].get("display") or ""
        if isinstance(txt, str) and txt.strip():
            return txt.strip()

    joined = " ".join(s.get("text", "") for s in segments).strip()
    return joined


class AzureSpeechTranscriber(BaseTranscriber):
    def __init__(self, storage: PgDataStorage, cfg: TranscriptionCfg):
        super().__init__(storage, cfg)

        internal = cfg.internal_cfg or {}

        self._model_system_name = internal.get("model_system_name")
        if not self._model_system_name:
            raise RuntimeError("Missing cfg.internal_cfg['model_system_name']")

        self._model_id = internal.get("model_id")
        if not self._model_id:
            raise RuntimeError("Missing cfg.internal_cfg['model_id']")

        self._language_code = (
            cfg.language.strip() if isinstance(cfg.language, str) else None
        )

        defaults = internal.get("defaults") or {}
        self._diarize = defaults.get("diarize")

        raw_ns = internal.get("num_speakers")
        self._num_speakers = int(raw_ns) if raw_ns else None

        raw_thr = internal.get("diarization_threshold")
        self._diarization_threshold = float(raw_thr) if raw_thr else None

        pre = internal.get("preprocess") or {}
        self._pre_sr = int(pre.get("sample_rate", 16000))

    async def _transcribe(self, file_id: str) -> Dict[str, Any]:
        src_url = await self._storage.get_audio_url(file_id)

        tmp_wav = await asyncio.to_thread(
            extract_audio_to_wav,
            src_path=src_url,
            sr=self._pre_sr,
        )

        raw_payload = None

        try:
            try:
                from ...services.ffmpeg import get_wav_duration_seconds

                duration = await asyncio.to_thread(get_wav_duration_seconds, tmp_wav)
                await self._storage._update_fields(
                    file_id, duration_seconds=float(duration)
                )
            except Exception:
                pass

            provider, model_cfg, model_id = await get_stt_provider_by_model(
                self._model_system_name
            )

            file_bytes = await asyncio.to_thread(_read_bytes, tmp_wav)

            safe_terms = _sanitize_keyterms(self._cfg.keyterms)

            raw_payload = await provider.speech_to_text_convert(
                file=file_bytes,
                model_id=model_id or self._model_id,
                diarize=self._diarize,
                language_code=self._language_code,
                num_speakers=self._num_speakers,
                diarization_threshold=self._diarization_threshold,
                keyterms=safe_terms or None,
                entity_detection=self._cfg.entity_detection,
                model_config=model_cfg,
            )

        finally:
            try:
                os.remove(tmp_wav)
            except OSError:
                pass

        payload = _to_dict(raw_payload) or {}

        _put_cached(file_id, payload)

        segments = _azure_payload_to_segments(payload)
        text = _azure_payload_to_text(payload, segments)

        return {"text": text, "segments": segments}
