from __future__ import annotations

import os
from typing import Any

from core.config.app import alchemy
from core.domain.providers.service import ProvidersService
from openai_model.utils import get_model_by_system_name

from .storage.postgres_storage import PgDataStorage
from .models import TranscriptionCfg, DiarizationCfg
from .pipeline import TranscriptionPipeline

from .transcribe.elevenlabs_transcribe.models import ElevenLabsTranscriber
from .diarize.elevenlabs_diarize.models import ElevenLabsDiarization

from .transcribe.azure_speech_transcribe.models import AzureSpeechTranscriber
from .diarize.azure_speech_diarize.models import AzureSpeechDiarization

from .transcribe.mistral_transcribe.models import MistralVoxtralTranscriber
from .diarize.mistral_diarize.models import MistralVoxtralDiarization


HF_KEY = os.getenv("HF_KEY", "")


def _deep_merge(a: dict[str, Any] | None, b: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(a or {})
    for k, v in (b or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def _is_provided(x: Any) -> bool:
    if x is None:
        return False
    if isinstance(x, str):
        s = x.strip().lower()
        return s not in ("", "null")
    return True


async def build_pipeline(
    storage: PgDataStorage,
    *,
    stt_model_system_name: str,
    language: str,
    number_of_participants: str | None = None,
    diarization_threshold: str | float | None = None,
    keyterms: list[str] | None = None,
    entity_detection: str | list[str] | None = None,
) -> TranscriptionPipeline:
    num_speakers: int | None = None
    if _is_provided(number_of_participants):
        num_speakers = int(number_of_participants)

    thr: float | None = None
    if _is_provided(diarization_threshold):
        thr = float(diarization_threshold)
        if not (0.1 <= thr <= 0.4):
            raise ValueError("diarization_threshold must be in [0.1, 0.4]")

    if num_speakers is not None and thr is not None:
        raise ValueError(
            "Provide either number_of_participants OR diarization_threshold, not both."
        )

    model_cfg = await get_model_by_system_name(stt_model_system_name)
    if not model_cfg:
        raise ValueError(f"STT model '{stt_model_system_name}' not found")

    provider_system_name = model_cfg.get("provider_system_name")
    if not isinstance(provider_system_name, str) or not provider_system_name:
        raise ValueError(
            f"Model '{stt_model_system_name}' does not have provider_system_name configured"
        )

    model_id = (
        model_cfg.get("ai_model") or model_cfg.get("model_id") or model_cfg.get("model")
    )
    if not isinstance(model_id, str) or not model_id:
        raise ValueError(f"Model '{stt_model_system_name}' is missing model id")

    model_meta = model_cfg.get("metadata_info") or {}
    model_defaults = model_meta.get("defaults") or {}
    model_pre = model_meta.get("preprocessing") or {}

    async with alchemy.get_session() as session:
        svc = ProvidersService(session=session)
        provider = await svc.get_one(system_name=provider_system_name)

        if not provider:
            raise ValueError(f"Provider '{provider_system_name}' not found")

        provider_type = str(provider.type or "")
        provider_meta = provider.metadata_info or {}
        provider_defaults = provider_meta.get("defaults") or {}
        provider_pre = (
            provider_meta.get("preprocessing")
            or (provider_meta.get("capabilities", {}) or {}).get("preprocessing")
            or {}
        )

    merged_defaults = _deep_merge(provider_defaults, model_defaults)
    merged_pre = _deep_merge(provider_pre, model_pre)

    preprocess_format = str(merged_pre.get("format", "wav"))
    preprocess_sr = int(merged_pre.get("sample_rate", 16_000))
    preprocess_mono = bool(merged_pre.get("mono", True))

    internal_cfg: dict[str, Any] = {
        "granularity": "word",
        "model_system_name": stt_model_system_name,
        "model_id": model_id,
        "preprocess": {
            "format": preprocess_format,
            "sample_rate": preprocess_sr,
            "mono": preprocess_mono,
        },
        "defaults": merged_defaults,
    }

    if num_speakers is not None:
        internal_cfg["num_speakers"] = num_speakers
    if thr is not None:
        internal_cfg["diarization_threshold"] = thr

    cfg = TranscriptionCfg(
        model=provider_type or "stt",
        language=language,
        number_of_participants=num_speakers,
        internal_cfg=internal_cfg,
        keyterms=keyterms,
        entity_detection=entity_detection,
    )

    if provider_type in ("elevenlabs_stt", "elevenlabs"):
        stt = ElevenLabsTranscriber(storage, cfg)
        diar_cfg = DiarizationCfg(
            model="elevenlabs",
            internal_cfg={
                **({"num_speakers": num_speakers} if num_speakers is not None else {}),
                **({"diarization_threshold": thr} if thr is not None else {}),
            },
        )
        dr = ElevenLabsDiarization(storage, diar_cfg)
        return TranscriptionPipeline(stt, dr, storage)

    if provider_type in ("azure_speech", "azure_speech_stt", "azure"):
        stt = AzureSpeechTranscriber(storage, cfg)
        diar_cfg = DiarizationCfg(
            model="azure_speech",
            internal_cfg={
                **({"num_speakers": num_speakers} if num_speakers is not None else {}),
                **({"diarization_threshold": thr} if thr is not None else {}),
            },
        )
        dr = AzureSpeechDiarization(storage, diar_cfg)
        return TranscriptionPipeline(stt, dr, storage)

    if provider_type in ("mistral_stt", "mistral-voxtral", "mistral"):
        stt = MistralVoxtralTranscriber(storage, cfg)
        dr = MistralVoxtralDiarization(storage, DiarizationCfg(model="mistral-voxtral"))
        return TranscriptionPipeline(stt, dr, storage)

    raise ValueError(
        f"Unsupported STT provider type '{provider_type}' "
        f"for model '{stt_model_system_name}' (provider '{provider_system_name}')"
    )
