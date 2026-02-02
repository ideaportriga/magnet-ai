from __future__ import annotations
from bson import ObjectId
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Literal


@dataclass(slots=True)
class FileData:
    """Persisted metadata for an uploaded audio file."""

    file_id: str = field(default_factory=lambda: str(ObjectId()))
    file_name: str = ""
    file_ext: str = ""
    content_type: str = ""
    object_key: str | None = None
    owner_id: Optional[str] = None
    status: Literal[
        "created",
        "started",
        "in_progress",
        "transcribed",
        "diarized",
        "completed",
        "failed",
    ] = "created"
    job_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    transcription: Optional[dict] = None
    error: Optional[str] = None

    @property
    def filename_with_ext(self) -> str:
        return f"{self.file_name}{self.file_ext}"

    @property
    def has_video(self) -> bool:
        return self.content_type.startswith("video/")


@dataclass(slots=True)
class DiarizationCfg:
    model: str = "mock"
    speakers: Optional[int] = None
    internal_cfg: Optional[dict] = None


@dataclass(slots=True)
class TranscriptionCfg:
    model: str
    language: Optional[str] = ""
    number_of_participants: Optional[int] = None
    internal_cfg: Optional[dict] = None
    diarization_cfg: Optional[DiarizationCfg] = None
    keyterms: list[str] | None = None
    entity_detection: str | list[str] | None = None


@dataclass(slots=True)
class DiarizationSegment:
    start: float
    end: float
    speaker: str
