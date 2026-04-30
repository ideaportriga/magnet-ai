from __future__ import annotations

import abc
from typing import ClassVar

from ..models import TranscriptionCfg
from ..storage.postgres_storage import PgDataStorage


ALLOWED_EXT = {".flac", ".m4a", ".mp3", ".ogg", ".wav", ".webm", ".mp4"}

# Soft cap on a single keyterm's character length. Anything longer than this
# is dropped uniformly across providers — long phrases rarely match useful
# acoustic regions and only inflate the prompt.
_MAX_KEYTERM_CHARS = 50


def _assert_supported(ext: str) -> None:
    """Raise if extension not in the allow-list."""
    if ext.lower() not in ALLOWED_EXT:
        raise ValueError(f"Unsupported audio format: {ext}")


class BaseTranscriber(abc.ABC):
    """Async interface for concrete transcribers.

    Concrete subclasses implement only `_transcribe(file_id)`; the
    surrounding pipeline orchestration (status updates, diarization,
    storage writes) lives in `TranscriptionPipeline.run`.
    """

    # Per-provider keyterm limits. Override in subclasses; `None` means
    # "no limit" (the keyterm passes through).
    MAX_KEYTERM_WORDS: ClassVar[int | None] = None
    MAX_KEYTERMS: ClassVar[int | None] = None

    def __init__(self, storage: PgDataStorage, cfg: TranscriptionCfg):
        self._storage = storage
        self._cfg = cfg

    @classmethod
    def _sanitize_keyterms(cls, keyterms: list[str] | None) -> list[str]:
        """Normalize keyterms into a provider-shaped list.

        Trims, drops empties / non-strings, applies the per-provider word and
        character caps, then truncates to ``MAX_KEYTERMS``.
        """
        if not keyterms:
            return []

        cleaned: list[str] = []
        for term in keyterms:
            if not isinstance(term, str):
                continue
            t = term.strip()
            if not t or len(t) > _MAX_KEYTERM_CHARS:
                continue
            if cls.MAX_KEYTERM_WORDS is not None:
                words = t.split()
                if len(words) > cls.MAX_KEYTERM_WORDS:
                    t = " ".join(words[: cls.MAX_KEYTERM_WORDS])
            cleaned.append(t)

        if cls.MAX_KEYTERMS is not None:
            cleaned = cleaned[: cls.MAX_KEYTERMS]
        return cleaned

    @abc.abstractmethod
    async def _transcribe(self, file_id: str) -> dict:
        """Return {"text": "...", "segments": [...] }."""
