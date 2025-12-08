from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Dict
import os
import asyncio
import json
import httpx

from ..base import BaseDiarization
from ...storage.postgres_storage import PgDataStorage
from ...models import DiarizationCfg
from ...services.ffmpeg import extract_audio_to_wav  # mono 16 kHz

# ---- ENV ----
SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY") or os.getenv("SPEECH_KEY", "")
SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION") or os.getenv("SPEECH_REGION", "")
SPEECH_ENDPOINT = os.getenv("AZURE_SPEECH_ENDPOINT") or os.getenv(
    "ENDPOINT", ""
)  # optional custom endpoint
API_VERSION = os.getenv("AZURE_SPEECH_API_VERSION", "2024-11-15")
DEFAULT_LOCALE = os.getenv("AZURE_SPEECH_LOCALE", "en-US")

# A conservative set of locales known to work well with FT diarization.
FT_DIAR_LOCALES = {
    "de-DE",
    "en-GB",
    "en-IN",
    "en-US",
    "es-ES",
    "es-MX",
    "fr-FR",
    "hi-IN",
    "it-IT",
    "ja-JP",
    "ko-KR",
    "pt-BR",
    "zh-CN",
}

# Timeouts
T_CONNECT = float(os.getenv("AZ_FAST_CONNECT_TIMEOUT", "30"))
T_READ = float(os.getenv("AZ_FAST_READ_TIMEOUT", "2400"))
T_WRITE = float(os.getenv("AZ_FAST_WRITE_TIMEOUT", "900"))
T_POOL = float(os.getenv("AZ_FAST_POOL_TIMEOUT", "60"))

# TODO - rework env variable handling
# if not (SPEECH_KEY and (SPEECH_REGION or SPEECH_ENDPOINT)):
#     raise RuntimeError("AZURE_SPEECH_KEY and either AZURE_SPEECH_REGION or AZURE_SPEECH_ENDPOINT are required")


@dataclass
class SpeakerSeg:
    start: float
    end: float
    speaker: str


class AzureFastDiarizer(BaseDiarization):
    """
    Azure Speech Fast Transcription diarization (sync, faster-than-RT).
    - Ensures mono 16 kHz WAV
    - Sends 'definition' with diarization enabled (+ optional min/max speakers)
    - Parses speaker IDs from the 'phrases' array
    - Renames to Guest-1/2/... for UI
    """

    def __init__(self, storage: PgDataStorage, cfg: DiarizationCfg):
        super().__init__(storage)
        self._storage = storage
        icfg = getattr(cfg, "internal_cfg", None) or {}

        # locale handling: use requested if in allow-list; else let FT pick (multilingual)
        requested = icfg.get("locale") or DEFAULT_LOCALE
        self.locale = requested if requested in FT_DIAR_LOCALES else None

        self.min_speakers: Optional[int] = _to_int(icfg.get("min_speakers"))
        self.max_speakers: Optional[int] = _to_int(icfg.get("max_speakers")) or _to_int(
            os.getenv("DIAR_MAX_SPEAKERS")
        )

        if SPEECH_ENDPOINT:
            base = SPEECH_ENDPOINT.rstrip("/")
            self._url = f"{base}/speechtotext/transcriptions:transcribe?api-version={API_VERSION}"
        else:
            self._url = f"https://{SPEECH_REGION}.api.cognitive.microsoft.com/speechtotext/transcriptions:transcribe?api-version={API_VERSION}"

    async def diarize(self, file_id: str) -> List[SpeakerSeg]:
        # 1) make mono 16k wav (doc allows many codecs, but mono wav is safest)
        src_bytes: bytes = await self._storage.load_audio(file_id)
        tmp_wav = await asyncio.to_thread(
            extract_audio_to_wav, src_path=None, src_bytes=src_bytes, sr=16_000
        )
        try:
            with open(tmp_wav, "rb") as f:
                wav_bytes = f.read()
        finally:
            try:
                os.remove(tmp_wav)
            except Exception:
                pass

        # 2) definition: diarization on; optional min/max; optional locales (or omit for multilingual)
        definition: Dict[str, object] = {"diarization": {"enabled": True}}
        if self.min_speakers:
            definition["diarization"]["minSpeakers"] = int(self.min_speakers)
        if self.max_speakers:
            definition["diarization"]["maxSpeakers"] = int(self.max_speakers)
        if self.locale:
            definition["locales"] = [self.locale]
        # else: omit 'locales' → FT uses multilingual model (still returns speakers)

        headers = {
            "Ocp-Apim-Subscription-Key": SPEECH_KEY,
            "User-Agent": "magnet-fast-diarizer/1.1",
        }
        timeout = httpx.Timeout(
            connect=T_CONNECT, read=T_READ, write=T_WRITE, pool=T_POOL
        )

        # 3) POST multipart (exactly like docs): files=audio, data=definition (stringified JSON)
        async with httpx.AsyncClient(timeout=timeout) as cli:
            resp = await cli.post(
                self._url,
                headers=headers,
                files={"audio": ("audio.wav", wav_bytes, "audio/wav")},
                data={"definition": json.dumps(definition)},
            )
            if resp.status_code >= 400:
                try:
                    detail = resp.json()
                except Exception:
                    detail = resp.text
                raise RuntimeError(
                    f"Fast Transcription error {resp.status_code}: {detail}"
                )

            payload = resp.json()

        # 4) Parse speakers from 'phrases' (primary), fallback to other shapes
        segs = _parse_phrases_first(payload)
        return _normalize_guest_labels(segs)


# ---------- helpers ----------


def _to_int(v) -> Optional[int]:
    try:
        return int(v) if v is not None and str(v).strip() != "" else None
    except Exception:
        return None


def _parse_phrases_first(payload: dict) -> List[SpeakerSeg]:
    """
    Prefer the 'phrases' array (each phrase has offset/duration and a 'speaker' id when diarization is on).
    Fallbacks:
      - 'combinedPhrases' (rarely carries speaker; mostly full text)
      - 'recognizedPhrases' with tick fields
    """
    segs: List[SpeakerSeg] = []

    # 1) New FT layout: 'phrases' with ms + 'speaker'
    phrases = payload.get("phrases")
    if isinstance(phrases, list) and phrases:
        for p in phrases:
            start = float(p.get("offsetMilliseconds", 0)) / 1000.0
            dur = float(p.get("durationMilliseconds", 0)) / 1000.0
            end = start + max(dur, 0.0)
            spk = p.get("speaker", None)
            segs.append(SpeakerSeg(start, end, str(spk) if spk is not None else ""))
        return _fuse_adjacent(segs)

    # 2) If we ever see speakers on combinedPhrases (uncommon), parse them
    cp = payload.get("combinedPhrases")
    if isinstance(cp, list) and cp:
        for p in cp:
            start = float(p.get("offsetMilliseconds", 0)) / 1000.0
            dur = float(p.get("durationMilliseconds", 0)) / 1000.0
            end = start + max(dur, 0.0)
            spk = p.get("speaker", None)
            segs.append(SpeakerSeg(start, end, str(spk) if spk is not None else ""))
        if segs:
            return _fuse_adjacent(segs)

    # 3) Legacy tick-based fallback
    def ticks_to_s(t: float) -> float:
        return float(t) / 10_000_000.0

    rp = payload.get("recognizedPhrases") or payload.get("recognitionResult", {}).get(
        "recognizedPhrases"
    )
    if isinstance(rp, list):
        for p in rp:
            off = p.get("offset") or p.get("offsetInTicks") or 0
            dur = p.get("duration") or p.get("durationInTicks") or 0
            start = ticks_to_s(off)
            end = start + ticks_to_s(dur)
            spk = p.get("speaker", None)
            segs.append(SpeakerSeg(start, end, str(spk) if spk is not None else ""))
    return _fuse_adjacent(segs)


def _fuse_adjacent(segs: List[SpeakerSeg], glue: float = 0.40) -> List[SpeakerSeg]:
    if not segs:
        return []
    segs.sort(key=lambda s: s.start)
    fused: List[SpeakerSeg] = []
    cur = segs[0]
    for nxt in segs[1:]:
        same_or_unknown = (
            (cur.speaker == nxt.speaker) or (not cur.speaker) or (not nxt.speaker)
        )
        if same_or_unknown and nxt.start <= cur.end + glue:
            cur = SpeakerSeg(
                cur.start, max(cur.end, nxt.end), cur.speaker or nxt.speaker
            )
        else:
            fused.append(cur)
            cur = nxt
    fused.append(cur)
    return fused


def _normalize_guest_labels(segs: List[SpeakerSeg]) -> List[SpeakerSeg]:
    """
    Turn numeric/empty speakers into Guest-1/2/... in order of first appearance.
    """
    mapping: Dict[str, str] = {}
    next_id = 1
    out: List[SpeakerSeg] = []
    for seg in segs:
        key = (seg.speaker or "").strip()
        if key == "" or key.lower() in {"u", "unk", "unknown"}:
            key = "__unknown__"
        if key not in mapping:
            mapping[key] = f"Guest-{next_id}"
            next_id += 1
        out.append(SpeakerSeg(seg.start, seg.end, mapping[key]))
    return out
