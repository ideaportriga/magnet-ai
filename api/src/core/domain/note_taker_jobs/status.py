"""Status vocabulary for `note_taker_jobs` rows.

These statuses describe a *preview job* lifecycle (admin UI), distinct from
transcription-pipeline statuses written to the `transcriptions` table
(`completed`, `transcribed`, `diarized`, `failed`) which are owned by
`speech_to_text/transcription/`.
"""

from __future__ import annotations

from enum import StrEnum


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    TRANSCRIBED = "transcribed"
    RERUNNING = "rerunning"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"

    @classmethod
    def is_terminal(cls, status: "str | JobStatus") -> bool:
        return cls(status) in {cls.COMPLETED, cls.FAILED, cls.TIMEOUT}

    @classmethod
    def can_rerun(cls, status: "str | JobStatus") -> bool:
        return cls(status) in {cls.COMPLETED, cls.FAILED, cls.TRANSCRIBED}

    @classmethod
    def in_flight(cls, status: "str | JobStatus") -> bool:
        return cls(status) in {cls.PENDING, cls.RUNNING, cls.RERUNNING}
