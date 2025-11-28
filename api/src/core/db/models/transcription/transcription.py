# transcriptions.py

from __future__ import annotations
from typing import Optional
from advanced_alchemy.base import AdvancedDeclarativeBase, CommonTableAttributes
from advanced_alchemy.mixins import AuditColumns
from advanced_alchemy.types import JsonB
from sqlalchemy import Float, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import text


class Transcription(
    CommonTableAttributes, AdvancedDeclarativeBase, AsyncAttrs, AuditColumns
):
    __tablename__ = "transcriptions"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        index=True,
    )

    file_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        comment="External file/job id used by API",
    )

    filename: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    file_ext: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    object_key: Mapped[Optional[str]] = mapped_column(Text(), nullable=True, index=True)
    content_type: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default=text("'started'"),
        index=True,
    )

    error: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    participants: Mapped[Optional[dict]] = mapped_column(JsonB, nullable=True)
    transcription: Mapped[Optional[dict]] = mapped_column(JsonB, nullable=True)
    full_text: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)

    def __repr__(self) -> str:
        return f"<Transcription file_id={self.file_id} status={self.status}>"
