from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class TranscriptionRead(BaseModel):
    """Read schema for a `transcriptions` row.

    Mirrors the dict shape historically returned by `PgDataStorage.get_meta`.
    Kept liberal (Any for JSONB columns) because old rows may be lists or dicts.
    """

    id: Optional[str] = None
    file_id: str
    filename: Optional[str] = None
    file_ext: Optional[str] = None
    object_key: Optional[str] = None
    content_type: Optional[str] = None
    duration_seconds: Optional[float] = None
    status: str = "started"
    error: Optional[str] = None
    participants: Optional[Any] = None
    transcription: Optional[Any] = None
    full_text: Optional[str] = None
    meeting_id: Optional[str] = None
    chat_id: Optional[str] = None
    initiated_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
