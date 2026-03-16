"""Tests for content_load_services (sync and async loaders)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.knowledge_graph.content_load_services import (
    load_content_from_bytes,
    load_content_from_bytes_async,
)
from services.knowledge_graph.models import ContentConfig, ContentReaderName


# ---------------------------------------------------------------------------
# Sync loader – load_content_from_bytes
# ---------------------------------------------------------------------------


class TestLoadContentFromBytes:
    def test_plain_text(self):
        config = ContentConfig(
            name="text",
            enabled=True,
            glob_pattern="*.txt",
            reader={"name": ContentReaderName.PLAIN_TEXT, "options": {}},
            chunker={"strategy": "recursive", "options": {}},
        )
        result = load_content_from_bytes(b"Hello World", config)
        assert result["text"] == "Hello World"

    def test_pdf_reader(self):
        with patch(
            "services.knowledge_graph.content_load_services.DefaultPdfReader"
        ) as MockReader:
            MockReader.return_value.extract_text_from_bytes.return_value = (
                "pdf content",
                3,
            )
            config = ContentConfig(
                name="pdf",
                enabled=True,
                glob_pattern="*.pdf",
                reader={"name": ContentReaderName.PDF, "options": {}},
                chunker={"strategy": "recursive", "options": {}},
            )
            result = load_content_from_bytes(b"fake-pdf", config)
            assert result["text"] == "pdf content"
            assert result["metadata"]["total_pages"] == 3

    def test_kreuzberg_raises(self):
        config = ContentConfig(
            name="doc",
            enabled=True,
            glob_pattern="*.docx",
            reader={"name": ContentReaderName.KREUZBERG, "options": {}},
            chunker={"strategy": "recursive", "options": {}},
        )
        with pytest.raises(ValueError, match="async"):
            load_content_from_bytes(b"data", config)

    def test_unsupported_reader(self):
        config = ContentConfig(
            name="unk",
            enabled=True,
            glob_pattern="*",
            reader={"name": "no_such_reader", "options": {}},
            chunker={"strategy": "recursive", "options": {}},
        )
        with pytest.raises(ValueError, match="Unsupported reader"):
            load_content_from_bytes(b"data", config)


# ---------------------------------------------------------------------------
# Async loader – load_content_from_bytes_async
# ---------------------------------------------------------------------------


class TestLoadContentFromBytesAsync:
    @pytest.mark.asyncio
    async def test_kreuzberg_reader(self):
        fake_reader = MagicMock()
        fake_reader.extract_from_bytes = AsyncMock(
            return_value=("extracted", {"total_pages": 5})
        )

        with patch(
            "services.knowledge_graph.content_load_services.KreuzbergReader",
            return_value=fake_reader,
        ):
            config = ContentConfig(
                name="doc",
                enabled=True,
                glob_pattern="*.docx",
                reader={"name": ContentReaderName.KREUZBERG, "options": {}},
                chunker={"strategy": "recursive", "options": {}},
            )
            result = await load_content_from_bytes_async(
                b"docx-bytes", config, filename="report.docx"
            )
            assert result["text"] == "extracted"
            assert result["metadata"]["total_pages"] == 5

    @pytest.mark.asyncio
    async def test_falls_back_to_sync_for_plain_text(self):
        config = ContentConfig(
            name="text",
            enabled=True,
            glob_pattern="*.txt",
            reader={"name": ContentReaderName.PLAIN_TEXT, "options": {}},
            chunker={"strategy": "recursive", "options": {}},
        )
        result = await load_content_from_bytes_async(b"sync-text", config)
        assert result["text"] == "sync-text"

    @pytest.mark.asyncio
    async def test_kreuzberg_mime_from_filename(self):
        """MIME type should be inferred from filename when not in options."""
        fake_reader = MagicMock()
        fake_reader.extract_from_bytes = AsyncMock(
            return_value=("text", {"total_pages": 1})
        )

        with patch(
            "services.knowledge_graph.content_load_services.KreuzbergReader",
            return_value=fake_reader,
        ):
            config = ContentConfig(
                name="html",
                enabled=True,
                glob_pattern="*.html",
                reader={"name": ContentReaderName.KREUZBERG, "options": {}},
                chunker={"strategy": "recursive", "options": {}},
            )
            await load_content_from_bytes_async(
                b"<html></html>", config, filename="page.html"
            )

            call_kwargs = fake_reader.extract_from_bytes.call_args
            assert call_kwargs[1]["mime_type"] == "text/html"
