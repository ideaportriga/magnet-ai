from __future__ import annotations
from .storage.postgres_storage import PgDataStorage
from .models import TranscriptionCfg, DiarizationCfg
from .transcribe.mock_transcribe.models import MockTranscriber
from .diarize.mock_diarize.models import MockDiarization
from .pipeline import TranscriptionPipeline
from .transcribe.azure_whisper.models import AzureWhisperTranscriber
from .transcribe.oracle_transcribe.models import OracleSpeechTranscriber
from .transcribe.whisper_http import WhisperHttpTranscriber
from .diarize.pyannote_http import PyAnnoteHttpDiarizer
from .transcribe.elevenlabs_transcribe.models import ElevenLabsTranscriber
from .diarize.elevenlabs_diarize.models import ElevenLabsDiarization
from .diarize.azure_conversation.models import AzureFastDiarizer
from .transcribe.oci_whisper.models import OciWhisperTranscriber
from .diarize.oci_speech.models import OciSpeechDiarizer
import os

HF_KEY = os.getenv("HF_KEY", "")


def _to_locale(lang: str) -> str:
    if not lang:
        return "en-US"
    if "-" in lang:
        return lang
    m = {"en": "en-US", "lv": "lv-LV", "ru": "ru-RU"}
    return m.get(lang.lower(), f"{lang.lower()}-{lang.upper()}")


def build_pipeline(
    kind: str,
    storage: PgDataStorage,
    language: str,
    number_of_participants: str | None = None,
    *,
    keyterms: list[str] | None = None,
    entity_detection: str | list[str] | None = None,
) -> TranscriptionPipeline:
    if kind == "mock":
        stt = MockTranscriber(storage, TranscriptionCfg(model="MOCK"))
        dr = MockDiarization(DiarizationCfg(model="mock"))
    elif kind == "whisper-mock":
        cfg = TranscriptionCfg(
            model="azure-whisper",
            language=language,
            internal_cfg={"deployment_id": "whisper", "granularity": "word"},
        )
        stt = AzureWhisperTranscriber(storage, cfg)
        dr = MockDiarization(DiarizationCfg(model="mock"))
    elif kind == "oracle-mock":
        cfg = TranscriptionCfg(
            model="oracle",
            language=language,
            internal_cfg={
                "granularity": "word",
            },
        )
        stt = OracleSpeechTranscriber(storage, cfg)
        dr = MockDiarization(DiarizationCfg(model="mock"))
    elif kind == "elevenlabs":
        cfg = TranscriptionCfg(
            model="elevenlabs",
            language=language,
            internal_cfg={"granularity": "word"},
            keyterms=keyterms,
            entity_detection=entity_detection,
        )
        stt = ElevenLabsTranscriber(storage, cfg)
        dr = ElevenLabsDiarization(storage, DiarizationCfg(model="elevenlabs"))
        return TranscriptionPipeline(stt, dr, storage)
    elif kind == "whisper-http-pyannote":
        stt = WhisperHttpTranscriber(
            storage, TranscriptionCfg(model="whisper-http", language=language)
        )
        dr = PyAnnoteHttpDiarizer(storage, DiarizationCfg(model="pyannote-http"))
    elif kind == "azure-whisper-azure-diar":
        cfg = TranscriptionCfg(
            model="azure-whisper",
            language=language,
            internal_cfg={"deployment_id": "whisper", "granularity": "word"},
        )
        stt = AzureWhisperTranscriber(storage, cfg)
        max_spk = int(number_of_participants) if number_of_participants else None
        dr = AzureFastDiarizer(
            storage,
            DiarizationCfg(
                model="azure-fast-diar",
                internal_cfg={
                    "locale": _to_locale(language),
                    "min_speakers": 2 if max_spk and max_spk >= 2 else None,
                    "max_speakers": max_spk or 2,
                },
            ),
        )
    elif kind == "oci-whisper-oci-diar":
        cfg = TranscriptionCfg(
            model="oci-whisper",
            language=language,
            number_of_participants=number_of_participants,
            internal_cfg={
                "granularity": "segment",
                "model_type": os.getenv("OCI_WHISPER_MODEL", "WHISPER_MEDIUM"),
            },
        )
        stt = OciWhisperTranscriber(storage, cfg)
        dr = OciSpeechDiarizer(storage, DiarizationCfg(model="oci-speech"))
    else:
        raise ValueError(f"Unknown pipeline kind {kind!r}")

    return TranscriptionPipeline(stt, dr, storage)
